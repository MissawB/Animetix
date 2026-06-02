# Remove Donations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Supprimer définitivement le modèle Django Donation, générer et appliquer sa migration de suppression en base de données, et nettoyer toutes les documentations associées.

**Architecture:** Suppression propre de modèle sans impact (le modèle n'est pas référencé ailleurs dans l'application) suivi d'une migration Django pour maintenir la cohérence de la base de données.

**Tech Stack:** Django, SQLite

---

### Task 1: Backend Cleanup

**Files:**
- Modify: `backend/api/animetix/models.py` (Delete lines 197-206)
- Modify: `backend/core/domain/services/health_dashboard_service.py` (Modify lines 24)

- [ ] **Step 1: Write the verification test before deletion**
  We want to ensure `Donation` is currently imported. We will check it with a quick check.
  Run: `python -c "from api.animetix.models import Donation; print(Donation)"`
  Expected: `<class 'api.animetix.models.Donation'>`

- [ ] **Step 2: Remove Donation model from models.py**
  In `backend/api/animetix/models.py`, delete the following lines:
  ```python
  class Donation(models.Model):
      user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
      amount = models.FloatField()
      currency = models.CharField(max_length=10, default="USD")
      platform = models.CharField(max_length=50, default="Ko-fi")
      message = models.TextField(blank=True)
      created_at = models.DateTimeField(auto_now_add=True)
      
      def __str__(self):
          return f"{self.amount} {self.currency} from {self.user.username if self.user else 'Anonymous'}"
  ```

- [ ] **Step 3: Modify health_dashboard_service.py to remove the comment comment**
  In `backend/core/domain/services/health_dashboard_service.py`, modify line 24 to remove any trace of the comment mentioning donations:
  Change:
  ```python
              "is_sustainable": False # Donations removed
  ```
  To:
  ```python
              "is_sustainable": False
  ```

- [ ] **Step 4: Verify Donation is no longer importable**
  Run: `python -c "from api.animetix.models import Donation"`
  Expected: FAIL with `ImportError: cannot import name 'Donation' from 'api.animetix.models'`

- [ ] **Step 5: Run Django checks**
  Run: `python backend/manage.py check`
  Expected: System check identified no issues (0 silenced).

- [ ] **Step 6: Commit**
  ```bash
  git add backend/api/animetix/models.py backend/core/domain/services/health_dashboard_service.py
  git commit -m "refactor: remove Donation model and references in backend"
  ```

---

### Task 2: Database Migration

**Files:**
- Create: Auto-generated Django migration in `backend/api/animetix/migrations/`

- [ ] **Step 1: Generate migration**
  Run: `python backend/manage.py makemigrations`
  Expected: Generated migration file dropping the Donation model.

- [ ] **Step 2: Apply migration**
  Run: `python backend/manage.py migrate`
  Expected: Applying animetix.0026_delete_donation... OK

- [ ] **Step 3: Verify the SQLite database schema no longer has animetix_donation table**
  Run: `sqlite3 backend/db.sqlite3 ".schema animetix_donation"`
  Expected: Empty output (table does not exist).

- [ ] **Step 4: Commit**
  ```bash
  git add backend/api/animetix/migrations/
  git commit -m "db: generate and apply migration to delete Donation table"
  ```

---

### Task 3: Documentation Cleanup

**Files:**
- Modify: `docs/TODO.md`
- Modify: `docs/HISTORY.md`

- [ ] **Step 1: Remove Support & Donation line from TODO.md**
  In `docs/TODO.md`, locate and delete the line:
  `- [ ] **Soutien & Dons (Donations)** : Créer une page \`/donate\` ou \`/support-us\` pour s'interfacer avec le modèle \`Donation\` existant (ex: intégration Ko-fi).`

- [ ] **Step 2: Remove Wall of Fame line from HISTORY.md**
  In `docs/HISTORY.md`, locate and delete the line:
  `- **Wall of Fame :** Déploiement de la page de soutien (\`SupportPage.tsx\`) listant les donateurs et les objectifs de financement du projet.`

- [ ] **Step 3: Commit documentation updates**
  ```bash
  git add docs/TODO.md docs/HISTORY.md
  git commit -m "docs: remove references to donations in TODO and HISTORY"
  ```
