# PACT — Rendu n°3

## Description du prototype et questionnaire utilisateurs

**Projet :** PACT — Protocol for Agent Coordination & Trust
**Date :** 11 mai 2026

---

## 1. Description détaillée du prototype

### 1.1 Vue d'ensemble

PACT est un **protocole de coordination** qui permet à des agents IA d'entreprises différentes de se découvrir, d'établir des relations de confiance et de collaborer de manière structurée. Le prototype prend la forme d'un **serveur API + dashboard temps réel** que l'on peut faire tourner localement, accompagné d'une démo de 4 agents autonomes pilotés par un LLM (Mercury 2 d'Inception Labs) qui exécutent le protocole de bout en bout sans intervention humaine.

Ce livrable est un **proof of concept** : le protocole est diffusé en **preview locale** (serveur et dashboard exécutés sur la machine de l'utilisateur, stockage en mémoire, pas de déploiement public), l'objectif étant de valider les mécanismes de coordination et de récolter des retours avant toute mise en production.

Le prototype matérialise les trois mécanismes du protocole :

1. **Handshake** — deux agents formalisent un partenariat via un *bond* signé cryptographiquement
2. **Discovery** — un agent diffuse une intention et le serveur identifie les agents dont les capacités correspondent
3. **Web of Trust** — un agent interroge ses partenaires bondés pour obtenir des recommandations par effet de réseau

### 1.2 Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| Enregistrement d'agents | Inscription d'un agent avec domaine, nom, clé publique Ed25519 et capacités déclarées |
| Vérification d'identité | Endpoint de vérification cryptographique de l'identité d'un agent |
| Bonds signés | Proposition + acceptation de partenariats avec signatures Ed25519 des deux parties |
| Templates d'interaction | Échanges structurés multi-étapes avec champs obligatoires validés côté serveur (`request_booking`, `request_quote`, `place_order`) |
| Broadcast d'intentions | Publication d'un besoin sur le réseau et matching automatique par capacités |
| Réseau de confiance | Recommandations pair-à-pair via traversée du graphe des bonds |
| Score de confiance | Calcul composite : bonds (15%/bond) + ancienneté (30%/an) + recommandations (10%/ref), plafonné à 1.0 |
| Dashboard temps réel | Graphe circulaire des agents, log d'activité cliquable, statistiques système, polling 2.5s |
| Démo IA autonome | 4 agents LLM qui exécutent le protocole de bout en bout en parallèle |
| Démo scriptée | Même scénario sans LLM (backup pour démos sans connexion API) |

### 1.3 Scénarios d'utilisation

**Scénario 1 — Formaliser un partenariat existant (Phase 1, Handshake)**

L'agent Vol et l'agent Hôtel collaborent déjà. Ils formalisent leur relation : Vol propose un bond avec des termes (`service=travel-coordination`, `sla=24h`, `data_format=JSON`), Hôtel signe à son tour, le bond devient actif. Vol lance ensuite une interaction `request_booking` (chambre Tokyo, dates, nombre de personnes) ; Hôtel confirme avec un `booking_id` et un prix ; Vol accepte. Toute l'interaction est cryptographiquement signée.

**Scénario 2 — Découvrir un nouveau partenaire (Phase 2, Discovery)**

Vol a besoin d'un loueur de voiture mais n'en connaît aucun. Il diffuse une intention avec les capacités requises (`car-rental`, `mobility`). L'agent Voiture, qui déclare ces capacités, voit l'intention via le matching automatique, répond, et Vol lui propose un bond. Aucun intermédiaire humain, aucun annuaire centralisé.

**Scénario 3 — Trouver un partenaire par recommandation (Phase 3, Web of Trust)**

L'agent Notes de Frais doit récupérer des factures d'hôtel mais ne diffuse pas son besoin. Il interroge son réseau bondé. Le serveur traverse le graphe : Notes de Frais → Vol (bondé) → Hôtel (bondé avec Vol, possède la capacité `accommodation`). Notes de Frais reçoit la recommandation avec le score de confiance d'Hôtel, propose un bond en citant la recommandation, Hôtel accepte. Le réseau passe de 3 bonds à 4 et devient pleinement connecté.

---

## 2. Description de la première expérience d'utilisation

Cette section décrit les manipulations qu'un utilisateur effectue pour découvrir le prototype, et les retours qu'il observe.

### 2.1 Installation et démarrage

| Manipulation | Retour du prototype |
|---|---|
| `uv sync` à la racine du projet | Installation des dépendances Python, message de succès `uv` |
| `uv run uvicorn src.pact.server:app` | Le serveur démarre sur le port 8000, log Uvicorn `Application startup complete` |
| Ouvrir `http://localhost:8000/docs` | Affichage de l'interface Swagger auto-générée listant les 40+ endpoints groupés par phase |
| `cd dashboard && npm install && npm run dev` | Le dashboard démarre sur le port 5173 (Vite) |
| Ouvrir `http://localhost:5173` | Affichage du dashboard vide : 0 agent, 0 bond, log d'activité vide |

### 2.2 Exécution de la démo IA

| Manipulation | Retour du prototype |
|---|---|
| `uv run python Demo/ai_demo.py` (dans un autre terminal) | Le terminal affiche une bannière colorée puis les 3 actes du scénario Tokyo |
| L'utilisateur observe le dashboard pendant que la démo tourne | Au bout d'1–2 secondes, 4 nœuds apparaissent dans le graphe circulaire (Vol, Hôtel, Voiture, Notes de Frais), les statistiques passent à 4 agents |
| La démo progresse dans l'Acte 1 (Handshake Vol↔Hôtel) | Une ligne pointillée animée se dessine entre Vol et Hôtel, le log d'activité ajoute les événements `bond.proposed`, `bond.accepted`, `interaction.created`, `message.sent` |
| L'utilisateur clique sur une ligne du log | La ligne s'étend et affiche les détails JSON de l'événement (termes du bond, payload du message, signatures) |
| L'Acte 2 (Discovery) se déroule | L'événement `intent.broadcast` apparaît dans le log, puis un nouveau bond apparaît entre Vol et Voiture |
| L'Acte 3 (Web of Trust) se déroule | L'événement `network.query` apparaît, puis un quatrième bond apparaît entre Notes de Frais et Hôtel. Les scores de confiance se mettent à jour (Vol grimpe le plus haut car il a le plus de bonds) |
| La démo se termine | Le terminal affiche le récapitulatif final avec les 4 agents, leurs scores de confiance et leur liste de bonds. Le graphe du dashboard est complet : 4 nœuds, 4 arêtes |

### 2.3 Exploration libre par l'utilisateur

| Manipulation | Retour du prototype |
|---|---|
| Tester un endpoint depuis Swagger (ex. `POST /agents/register`) | Réponse 200 avec l'agent créé et son ID, ou erreur 422 avec le détail du champ manquant |
| Proposer un bond avec une signature invalide | Réponse 400 du serveur avec le message `invalid signature` (la signature Ed25519 est vérifiée à la réception) |
| Redémarrer le serveur | Toutes les données disparaissent (stockage en mémoire), le dashboard revient à l'état vide — choix assumé pour ce PoC |
| Lancer `Demo/demo.py` (version sans LLM) | Même scénario que la démo IA mais déterministe et instantané, utile pour démontrer sans dépendance API externe |

---

## 3. Questionnaire utilisateurs

Le questionnaire ci-dessous sera envoyé à des futurs utilisateurs (développeurs d'agents IA, étudiants, profils techniques) après qu'ils aient lancé la démo. Pour chaque question, on précise le **bénéfice attendu** : ce qu'on cherche à valider, infirmer ou apprendre.

### 3.1 Compréhension du produit

**Q1 — En une phrase, comment décririez-vous à un collègue ce que fait PACT ?**
*Format : texte libre.*
**Bénéfice :** mesurer si le pitch est compris sans effort. Si les réponses convergent vers "coordination entre agents IA", la value proposition passe. Si elles divergent ou restent floues, il faut retravailler la communication (README, dashboard, narration de la démo).

**Q2 — Sur une échelle de 1 à 5, à quel point le problème résolu par PACT vous paraît-il réel et important ?**
*Format : échelle 1 à 5.*
**Bénéfice :** valider que le problème "touriste vs. local" résonne au-delà de l'équipe projet. Une moyenne < 3 indique qu'il faut réorienter le discours vers un cas d'usage plus tangible.

### 3.2 Expérience de la démo

**Q3 — Avez-vous réussi à lancer la démo du premier coup ? Si non, à quelle étape avez-vous bloqué ?**
*Format : oui/non + texte libre.*
**Bénéfice :** identifier les points de friction du onboarding (dépendances, variables d'environnement, ordre des commandes). Chaque blocage cité = un correctif à apporter dans le README ou un script d'install.

**Q4 — Sur le dashboard, quelles informations avez-vous regardées en premier ? Lesquelles n'avez-vous pas comprises ?**
*Format : texte libre.*
**Bénéfice :** hiérarchiser le contenu du dashboard. Ce qui est regardé en premier doit être mis en avant, ce qui n'est pas compris doit être expliqué (tooltip, légende) ou supprimé.

**Q5 — Avez-vous cliqué sur les lignes du log d'activité pour voir les détails ? Si oui, l'information affichée vous a-t-elle été utile ?**
*Format : oui/non + texte libre.*
**Bénéfice :** valider la fonctionnalité "drill-down" du log. Si peu d'utilisateurs cliquent, il faut rendre l'affordance plus visible. Si l'info affichée n'est pas utile, il faut revoir le format (JSON brut vs. mise en forme).

### 3.3 Mécanismes du protocole

**Q6 — Parmi les trois mécanismes (Handshake, Discovery, Web of Trust), lequel vous semble le plus utile ? Le moins utile ?**
*Format : QCM à classer.*
**Bénéfice :** prioriser les efforts futurs. Si le Web of Trust ressort comme le plus utile, on investit sur la profondeur du graphe et le scoring multi-saut. Si le Handshake suffit à 80% des cas, on peut alléger les phases 2 et 3.

**Q7 — Le score de confiance est calculé à partir du nombre de bonds, de leur ancienneté et des recommandations reçues. Cette formule vous paraît-elle juste ? Que changeriez-vous ?**
*Format : texte libre.*
**Bénéfice :** challenger le modèle de trust. Les retours peuvent faire émerger des signaux manquants (taux d'interactions réussies, montant en jeu, fraîcheur des interactions) à intégrer dans la v2 du score.

**Q8 — Les templates d'interaction (`request_booking`, `request_quote`, `place_order`) couvrent-ils des cas d'usage qui vous intéressent ? Quels templates supplémentaires aimeriez-vous voir ?**
*Format : texte libre.*
**Bénéfice :** alimenter le backlog de templates. Les templates les plus demandés (paiement, dispute, signature de document) deviendront prioritaires.

### 3.4 Confiance et sécurité

**Q9 — Les bonds et les messages sont signés en Ed25519. Cette garantie cryptographique est-elle suffisante pour que vous fassiez confiance au protocole en production ?**
*Format : oui/non + texte libre.*
**Bénéfice :** détecter les attentes implicites en matière de sécurité (PKI complète, audit log immuable, révocation de clés). Permet de planifier les ajouts nécessaires pour passer du PoC à un produit déployable.

**Q10 — Imaginez qu'un agent malveillant tente d'usurper l'identité d'un agent légitime. Quels mécanismes attendez-vous de PACT pour empêcher cela ?**
*Format : texte libre.*
**Bénéfice :** confronter notre modèle d'identité (domain-based + clé publique) aux attentes des utilisateurs. Si beaucoup citent DNS-TXT ou TLS, on confirme la roadmap d'identité ; si d'autres attentes émergent (DID, attestation OIDC), on les évalue.

### 3.5 Intégration et adoption

**Q11 — Sur une échelle de 1 à 5, à quel point seriez-vous prêt à intégrer PACT dans un agent IA que vous développez ?**
*Format : échelle 1 à 5 + raison.*
**Bénéfice :** mesurer l'intent-to-adopt. Si la note est haute mais qu'aucun n'agit, on a un problème de friction. Si elle est basse, on a un problème de valeur perçue.

**Q12 — Quel serait, pour vous, le bloquant principal à utiliser PACT dans un produit réel ? (technique, légal, business, autre)**
*Format : texte libre.*
**Bénéfice :** identifier le frein le plus structurant. Si le bloquant principal est technique (manque de SDK TypeScript, pas de hosting managé), c'est actionnable rapidement. Si c'est légal (qui est responsable d'un bond signé par un agent ?), c'est une roadmap stratégique.

**Q13 — Préféreriez-vous utiliser PACT comme : (a) une bibliothèque que vous intégrez vous-même, (b) un service managé hébergé, (c) un standard ouvert que plusieurs fournisseurs implémentent ?**
*Format : QCM, un seul choix.*
**Bénéfice :** orienter la stratégie de distribution. Le résultat majoritaire détermine la suite : SDK polish, offre SaaS, ou démarche de standardisation (groupe de travail, RFC).

### 3.6 Ouvert

**Q14 — Quelle est la chose qui vous a le plus surpris (en bien ou en mal) en testant PACT ?**
*Format : texte libre.*
**Bénéfice :** capter les signaux faibles que les questions fermées ratent. Les surprises positives indiquent des points différenciants à amplifier ; les surprises négatives, des bugs ou angles morts à corriger.

**Q15 — Si vous deviez ajouter UNE fonctionnalité à PACT, ce serait laquelle ?**
*Format : texte libre.*
**Bénéfice :** prioriser le backlog par la demande. Les demandes qui reviennent plusieurs fois passent en haut de la roadmap pour les itérations post-questionnaire.

---

## 4. Suite

Les réponses au questionnaire (cible : au moins 5 répondants) seront analysées d'ici fin mai. Les trois améliorations les plus fréquemment demandées seront implémentées avant le showroom du 4 juin, conformément au planning établi lors de la réunion de suivi du 20 mars.
