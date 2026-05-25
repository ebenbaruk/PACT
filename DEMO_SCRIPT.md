# PACT — Script de démo (présentation aux juges)

> **3 mini-démos indépendantes**, une par mécanisme. Chacune = **3 clics**, 2-3 agents. On peut les montrer dans l'ordre (1 → 2 → 3, complexité croissante) ou n'en présenter qu'une. Compte ~1 min par mini-démo.

---

## En une phrase

**PACT, c'est le « HTTP/IP des agents IA d'entreprises » :** un protocole qui permet à des agents IA de **différentes entreprises** de se découvrir, prouver leur identité, se faire confiance et collaborer — **automatiquement, sans annuaire central ni humain**, et de façon **signée et auditable**.

---

## Le problème (≈ 15 s)

Quand deux IA de deux entreprises différentes doivent collaborer, **il n'existe aucun standard** : aucun moyen fiable de se découvrir, de prouver qui on est, de formaliser un accord, ni de savoir à qui faire confiance. PACT comble ce vide. On le démontre avec **3 mécanismes**, chacun isolé dans une mini-démo.

---

## Le décor : des agents = des entreprises

Chaque agent est l'**agent IA d'une entreprise** (piloté par le modèle Mercury 2). On utilise quatre rôles d'entreprise très simples :

| Agent | Entreprise |
|---|---|
| 🏭 **Acheteur** | une entreprise qui achète |
| 🔧 **Fournisseur** | un fournisseur de pièces |
| 🚚 **Logistique** | un transporteur |
| 📊 **Comptable** | un service de facturation |

**À dire :** ce sont de **vrais agents IA** — à chaque clic, **Mercury 2 décide** lui-même de l'action (badge `🧠 Mercury 2`). À gauche on voit **ce que l'agent pense et envoie** ; à droite, **le réseau de confiance se construit en direct**. Tout est **signé** (Ed25519).

---

## Mini-démo 1 — Handshake · *sceller un accord infalsifiable*

> **Le problème :** un Acheteur et un Fournisseur qui ne se connaissent pas veulent faire affaire. Comment sceller un accord que ni l'un ni l'autre ne peut falsifier ni renier ?

1. **Clic 1** — Les deux agents rejoignent le réseau et publient leur **identité signée** (clé Ed25519).
2. **Clic 2** — L'**Acheteur propose un accord signé** au Fournisseur (service, prix, délai). Sa signature engage son identité.
3. **Clic 3** — Le **Fournisseur vérifie la signature et contre-signe**. Le lien devient **actif, infalsifiable, opposable**.

> **Punchline :** deux entreprises inconnues ont un **contrat numérique vérifiable**, sans tiers de confiance.

---

## Mini-démo 2 — Discovery · *se trouver sans annuaire*

> **Le problème :** l'Acheteur a besoin d'un transporteur mais n'en connaît aucun, et il n'existe **aucun annuaire central**. Comment trouver le bon partenaire ?

1. **Clic 1** — Deux agents sur le réseau, **sans aucun lien** entre eux.
2. **Clic 2** — L'Acheteur **diffuse son besoin** de transport à tout le réseau *(un anneau part de son agent)*.
3. **Clic 3** — Un agent **Logistique, jamais sollicité**, voit que ses capacités correspondent, **répond**, et les deux **nouent un partenariat**.

> **Punchline :** deux agents se sont trouvés **tout seuls, par capacité** — sans annuaire ni intermédiaire humain.

---

## Mini-démo 3 — Web of Trust · *la confiance se propage*

> **Le problème :** l'Acheteur a besoin d'un service de facturation mais **ne veut pas traiter avec un inconnu**. Il s'appuie sur ceux en qui il a déjà confiance.

1. **Clic 1** — **Réseau de confiance existant** : Acheteur ↔ Fournisseur ↔ Comptable. *L'Acheteur ne connaît PAS le Comptable.* (C'est le point de départ assumé.)
2. **Clic 2** — L'Acheteur **interroge son réseau** : « qui connaît un service de facturation fiable ? » → le chemin **Acheteur → Fournisseur → Comptable se surligne**, et le Comptable est **recommandé (via le Fournisseur)**.
3. **Clic 3** — L'Acheteur **propose un accord au Comptable en citant la recommandation** ; le Comptable accepte.

> **Punchline :** la confiance se propage **de proche en proche** — une recommandation entre partenaires suffit à créer un nouveau lien fiable.

---

## La conclusion (≈ 15 s)

> *« Trois mécanismes, trois briques : **prouver et sceller** un accord (Handshake), **se découvrir** sans annuaire (Discovery), **se recommander** par la confiance (Web of Trust). Mises bout à bout, elles laissent des agents d'entreprises différentes collaborer **sans humain, sans plateforme centrale, et de façon auditable**. C'est ça, PACT. »*

---

## ⚠️ Ce qu'il NE FAUT PAS changer / précautions

- **Ne redémarre PAS le serveur pendant la démo.** L'état est en mémoire ; utilise le bouton **↺** (recommencer une mini-démo) ou **← Menu** pour changer.
- **Garde `INCEPTION_API_KEY` dans `.env`.** Avec la clé → badge `🧠 Mercury 2` (raisonnement IA réel). Sans → badge `⚠️ secours` (**mode scripté de secours : la démo marche quand même** si le wifi/API lâche).
- **Mini-démo 3, clic 1 :** les deux liens de confiance préalables (Acheteur↔Fournisseur, Fournisseur↔Comptable) sont créés volontairement — **c'est le point de départ** de la démonstration, pas un raccourci.
- **Lance chaque démo une fois avant de présenter** (réchauffe l'API).
- **Le bouton ◀** sert à *revoir* une étape ; **Suivant** avance toujours.

---

## Démarrer

```bash
# terminal 1 — le serveur (protocole + dashboard)
uv run uvicorn src.pact.server:app

# terminal 2 — le dashboard
cd dashboard && npm run dev
```

Ouvre **http://localhost:5173** → choisis une mini-démo (carte ou onglet en haut) → **Suivant** à chaque étape.

---

## Anti-sèche — questions probables des juges

- **« Et si un agent ment sur son identité ? »** → Identité = domaine + clé publique Ed25519 ; chaque accord et chaque message est **signé**, donc vérifiable. *(Roadmap : ancrage DNS-TXT / DID.)*
- **« Pourquoi pas juste une API REST ? »** → PACT standardise **la découverte + la confiance + l'audit** entre acteurs **qui ne se connaissent pas d'avance**, pas seulement l'échange de données.
- **« C'est local / en mémoire ? »** → PoC **volontairement local** pour valider les mécanismes avant déploiement.
- **« Le score de confiance ? »** → Composite : nombre de liens + ancienneté + recommandations reçues, plafonné à 1,0.
