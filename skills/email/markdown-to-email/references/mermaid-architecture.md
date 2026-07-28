# Mermaid Architecture Diagram for HermesDeck Lead Emails

Use this to visually explain the workflow agent + agentic harness architecture.

## Diagram (MMD format)

```mermaid
flowchart TB
    subgraph Sources["Sources"]
        A1["Smart Contracts"]:::source
        A2["CRM / Base client"]:::source
        A3["Reseaux sociaux"]:::source
        A4["Emails"]:::source
    end

    subgraph Harness["Harnais Agentique"]
        B1["Agent Collecte"]:::agent
        B2["Agent Analyse"]:::agent
        B3["Agent Redaction"]:::agent
        B4["Agent Decision"]:::agent
        C["Orchestrateur"]:::orchestrator
    end

    subgraph Outputs["Delivrables"]
        D1["Rapports"]:::output
        D2["Alertes"]:::output
        D3["Relances"]:::output
    end

    A1 --> B1; A2 --> B1; A3 --> B1; A4 --> B1
    B1 --> B2 --> B3 --> B4
    C -.-> B1; C -.-> B2; C -.-> B3; C -.-> B4
    B4 --> D1; B4 --> D2; B4 --> D3

    classDef source fill:#1a1a2e,stroke:#f7931a,color:#e6e6e6
    classDef agent fill:#16213e,stroke:#58a6ff,color:#c9d1d9
    classDef orchestrator fill:#0f3460,stroke:#f7931a,color:#e6e6e6,stroke-width:3px
    classDef output fill:#1a1a2e,stroke:#3fb950,color:#c9d1d9
```

## Color Scheme

| Element | Class | Hex |
|---|---|---|
| Sources | source | #f7931a (orange) |
| Agents | agent | #58a6ff (blue) |
| Orchestrator | orchestrator | #f7931a bold (orange) |
| Outputs | output | #3fb950 (green) |
| Background | subgraph | #0d1117 |

## Rendering

The .mmd file can be rendered using any Mermaid-compatible viewer
(mermaid.live, GitHub markdown, etc.). Include the rendered version
as an SVG attachment in the email.