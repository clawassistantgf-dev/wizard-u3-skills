#!/usr/bin/env python3
"""
quality-loop.py — Orchestrateur LLM-as-Judge.
Usage:
  python3 quality-loop.py --task "Décris Bitcoin en 3 phrases" --criteria poetry
  python3 quality-loop.py --task "Code un fibonacci récursif" --criteria code
  python3 quality-loop.py --task "Analyse ce code" --criteria analysis

Lit les fichiers de config/critères/prompts dans ~/.hermes/skills/quality-loop/
Ne modifie que les fichiers .txt/.yaml pour changer le comportement.
"""

import argparse, json, os, re, subprocess, sys, yaml, shutil
from datetime import datetime

# === Chemins ===
HOME = os.path.expanduser("~")
SKILL_DIR = f"{HOME}/.hermes/skills/quality-loop"
CONFIG_PATH = f"{SKILL_DIR}/config.yaml"
CRITERIA_DIR = f"{SKILL_DIR}/criteria"
PROMPTS_DIR = f"{SKILL_DIR}/prompts"
LOG_FILE = f"{HOME}/.hermes/quality-loop-logs.jsonl"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def read_file(path):
    with open(path) as f:
        return f.read()

def call_hermes(prompt, timeout=60):
    """Appelle Hermes en mode silencieux et retourne la réponse."""
    result = subprocess.run(
        ["hermes", "chat", "-q", prompt, "-Q"],
        capture_output=True, text=True, timeout=timeout
    )
    return (result.stdout or result.stderr or "").strip()

def parse_judge(response):
    """Extrait SCORE, FEEDBACK, PASS de la réponse du juge."""
    score_m = re.search(r'SCORE:\s*(\d+)/10', response)
    pass_m  = re.search(r'PASS:\s*(YES|NO)', response, re.IGNORECASE)
    fb_m    = re.search(r'FEEDBACK:\s*(.+?)(?=PASS:|$)', response, re.DOTALL)
    
    return {
        "score": int(score_m.group(1)) if score_m else 0,
        "passed": pass_m.group(1).upper() == "YES" if pass_m else False,
        "feedback": fb_m.group(1).strip()[:300] if fb_m else "",
        "raw": response[:300],
    }

def log_round(entry):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def main():
    parser = argparse.ArgumentParser(description="Boucle qualité LLM-as-Judge")
    parser.add_argument("--task", required=True, help="La tâche à accomplir")
    parser.add_argument("--criteria", default="code", 
                        help="Nom du fichier critères (dans criteria/)")
    parser.add_argument("--max-rounds", type=int, default=None)
    parser.add_argument("--threshold", type=int, default=None)
    parser.add_argument("--judge-model", default="", help="Modèle pour le juge")
    args = parser.parse_args()

    config = load_config()
    max_rounds = args.max_rounds or config.get("max_rounds", 3)
    threshold = args.threshold or config.get("threshold", 8)

    # Charger le template juge et les critères
    judge_template = read_file(f"{PROMPTS_DIR}/judge_default.txt")
    
    criteria_path = f"{CRITERIA_DIR}/{args.criteria}.txt"
    if not os.path.exists(criteria_path):
        print(f"❌ Critères introuvables : {criteria_path}")
        print(f"   Disponibles : {[f.replace('.txt','') for f in os.listdir(CRITERIA_DIR) if f.endswith('.txt')]}")
        sys.exit(1)
    criteria = read_file(criteria_path)

    print(f"═" * 50)
    print(f"🧙 QUALITY LOOP")
    print(f"═" * 50)
    print(f"Tâche  : {args.task}")
    print(f"Critères: {args.criteria}")
    print(f"Seuil  : {threshold}/10  |  Rounds: {max_rounds}")
    print(f"═" * 50)

    output = ""
    history = []
    start_time = datetime.now()

    for round_num in range(1, max_rounds + 1):
        print(f"\n─── Round {round_num}/{max_rounds} ───")

        # Étape 1 : Produire
        producer_prompt = args.task
        if history:
            last_feedback = history[-1].get("feedback", "")
            if last_feedback and config.get("inject_feedback", True):
                producer_prompt += (
                    f"\n\nRETOUR DU JUGE AU ROUND PRÉCÉDENT : {last_feedback}"
                    f"\nAméliore ta réponse en tenant compte de ce retour."
                )
        
        print(f"🤖 Production...")
        try:
            output = call_hermes(producer_prompt)
        except subprocess.TimeoutExpired:
            print("⏰ Timeout production")
            break

        # Étape 2 : Juger
        judge_prompt = judge_template.format(
            task=args.task, output=output, criteria=criteria, threshold=threshold
        )
        
        print(f"⚖️  Jugement...")
        try:
            judge_response = call_hermes(judge_prompt)
        except subprocess.TimeoutExpired:
            print("⏰ Timeout juge")
            break

        result = parse_judge(judge_response)
        result["round"] = round_num
        result["output"] = output[:200]
        history.append(result)
        log_round({
            "task": args.task, "round": round_num, "time": datetime.now().isoformat(),
            **result
        })

        print(f"   Score : {result['score']}/10")
        print(f"   PASS  : {'✅' if result['passed'] else '❌'} {result['passed']}")
        print(f"   Avis  : {result['feedback'][:120]}")

        # Étape 3 : Décision
        if result["passed"]:
            print(f"\n✅ Qualité atteinte (≥{threshold}/10) au round {round_num}")
            
            # Self-check : demander à l'agent de confirmer
            final_check_prompt = (
                f"Tâche : {args.task}\n\n"
                f"Réponse produite :\n{output}\n\n"
                f"Le LLM-as-Judge a donné {result['score']}/10 et considère "
                f"la qualité suffisante.\n"
                f"⚠️  À TOI DE DÉCIDER : estimes-tu que la tâche est terminée ?\n"
                f"Réponds UNIQUEMENT : FINI ou PAS FINI + 1 phrase expliquant pourquoi."
            )
            try:
                final_check = call_hermes(final_check_prompt)
            except subprocess.TimeoutExpired:
                final_check = "PAS FINI (timeout)"
            
            if "FINI" in final_check.upper()[:20]:
                duration = (datetime.now() - start_time).total_seconds()
                summary = generate_summary(args, history, output, round_num, max_rounds, duration, True)
                print(summary)
                # Sauvegarder le rapport markdown
                report_path = f"{HOME}/.hermes/quality-loop-report.md"
                with open(report_path, "w") as f:
                    f.write(summary)
                print(f"\n📝 Rapport sauvegardé : {report_path}")
                sys.exit(0)
            else:
                print(f"⚠️  Agent PAS FINI : {final_check[:120]}")
                print(f"   → Round supplémentaire avec les retours combinés.")
        else:
            print(f"⬇️  Score < seuil → round suivant avec feedback")

    # Sortie après max_rounds
    duration = (datetime.now() - start_time).total_seconds()
    summary = generate_summary(args, history, output, max_rounds, max_rounds, duration, False)
    print(summary)
    report_path = f"{HOME}/.hermes/quality-loop-report.md"
    with open(report_path, "w") as f:
        f.write(summary)
    print(f"\n📝 Rapport sauvegardé : {report_path}")

def generate_summary(args, history, final_output, rounds_done, max_rounds, duration, passed):
    """Génère un rapport markdown de la session."""
    lines = []
    lines.append("# 🧙 Quality Loop — Rapport")
    lines.append("")
    lines.append(f"**Tâche** : {args.task}")
    lines.append(f"**Critères** : {args.criteria}")
    lines.append(f"**Seuil** : {args.threshold or 8}/10")
    lines.append(f"**Rounds** : {rounds_done}/{max_rounds}  |  **Durée** : {duration:.0f}s")
    lines.append(f"**Résultat** : {'✅ PASS' if passed else '⏹️  MAX ROUNDS'}")
    lines.append("")
    lines.append("## 📊 Scores par round")
    lines.append("")
    lines.append("| Round | Score | PASS | Feedback |")
    lines.append("|-------|-------|------|----------|")
    for h in history:
        emoji = "✅" if h["passed"] else "❌"
        fb = h.get("feedback", "")[:80]
        lines.append(f"| {h['round']} | {h['score']}/10 | {emoji} | {fb} |")
    
    if len(history) > 1:
        scores = [h["score"] for h in history]
        delta = scores[-1] - scores[0]
        lines.append("")
        lines.append(f"**Progression** : {scores[0]}/10 → {scores[-1]}/10 ({delta:+d} pts)")
    
    lines.append("")
    lines.append("## 🏁 Résultat final")
    lines.append("")
    lines.append("```")
    lines.append(final_output[:800])
    lines.append("```")
    lines.append("")
    if passed:
        lines.append("✅ Qualité atteinte — l'agent a confirmé la fin de la tâche.")
    else:
        lines.append("⏹️  Nombre maximum de rounds atteint sans atteindre le seuil.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Quality Loop — {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")
    return "\n".join(lines)

if __name__ == "__main__":
    main()