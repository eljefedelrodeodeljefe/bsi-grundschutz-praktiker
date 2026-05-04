# BSI IT-Grundschutz Praktiker — Prüfungstrainer

Prüfungstrainer für die [BSI IT-Grundschutz Praktiker](https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/Zertifizierte-Informationssicherheit/IT-Grundschutzschulung/Online-Kurs-IT-Grundschutz/online-kurs-it-grundschutz_node.html) Zertifizierung. Fragen und Antworten werden direkt vom offiziellen BSI-Online-Kurs gescrapt.

## Why IT-Grundschutz?

Most security frameworks tell you _what_ to achieve; IT-Grundschutz tells you _how_.

**ISO 27001** is principle-based: Annex A lists 93 controls written at a high level of abstraction. Deciding what "A.8.8 Management of technical vulnerabilities" actually means for a specific Linux server is left entirely to you and your auditor. **NIST CSF** and **SOC 2** have the same property — they describe outcomes, not implementations.

The [IT-Grundschutz-Kompendium](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/IT-GS-Kompendium/IT_Grundschutz_Kompendium_Edition2023.pdf) takes a different approach. It ships ~100 _Bausteine_ (building blocks), each scoped to a concrete asset type — `SYS.1.1 Allgemeiner Server`, `NET.1.1 Netzarchitektur`, `OPS.1.1.3 Patch- und Änderungsmanagement`, and so on. Every Baustein lists specific, auditable requirements in three tiers:

| Tier                                        | Audience                           |
| ------------------------------------------- | ---------------------------------- |
| **Basis-Anforderungen**                     | Every organisation, non-negotiable |
| **Standard-Anforderungen**                  | Normal protection needs            |
| **Anforderungen bei erhöhtem Schutzbedarf** | High-risk environments             |

The result is that after a Strukturanalyse you can map every asset in your environment to a Baustein and get a concrete checklist rather than a principles document. That directness is what makes Grundschutz unusually implementable in practice.

A further advantage: BSI provides an [officially recognised mapping](https://www.bsi.bund.de/DE/Themen/Unternehmen-und-Organisationen/Standards-und-Zertifizierung/IT-Grundschutz/Zertifizierte-Informationssicherheit/Zertifizierung-nach-IS-Grundschutz/ISO-27001-Zertifizierung/iso-27001-zertifizierung_node.html) from Grundschutz to ISO 27001, so a Grundschutz implementation can be certified against both standards simultaneously.

## Setup

```bash
just install
```

## Usage

```bash
just scrape   # fetch questions from bsi.bund.de → data/questions.json
just quiz     # run the quiz (default: just)
just all      # scrape + quiz in one go
```

The scraper covers all 8 lessons that have a test (Lektion 1 has no test):

| Lektion | Kategorie                          |
| ------- | ---------------------------------- |
| 2       | Sicherheitsmanagement              |
| 3       | Strukturanalyse                    |
| 4       | Schutzbedarfsfeststellung          |
| 5       | Modellierung                       |
| 6       | IT-Grundschutz-Check               |
| 7       | Risikoanalyse                      |
| 8       | Umsetzungsplanung                  |
| 9       | Aufrechterhaltung und Verbesserung |

## Quiz flow

1. Pick a category (or all 48 questions at once)
2. Optionally shuffle
3. Read the question → select answers with **Space**, press **Enter** to submit
4. See correct answers revealed with ✓/✗ feedback
5. Score and weak-spot table at the end; results persist across sessions
