# Améliorer la Délivrabilité des Emails

Les emails GeoAnnotator arrivent parfois dans les spams. Voici comment améliorer la délivrabilité.

## ✅ Changements Déjà Effectués

1. **Message d'avertissement ajouté** dans tous les emails :
   ```
   📬 NOTE: If you don't see this email in your inbox, please check your spam/junk folder.
   ```

2. **Templates mis à jour** :
   - `confirm_registration.html/txt` (inscription)
   - `confirm_email_change.html/txt` (changement email)
   - `confirm_account_deletion.html/txt` (suppression compte)

---

## 🔧 Configuration Mailjet pour Éviter les Spams

### 1. Vérifier le Domaine d'Envoi (IMPORTANT ⭐)

**Actuellement** : `geoannotator.noreply@gmail.com`
**Problème** : Gmail dans FROM mais envoyé via Mailjet → suspect pour les filtres anti-spam

**Solution** : Utiliser votre propre domaine

#### Option A : Domaine Personnel (Recommandé)
```
noreply@geoannotator.com
contact@geoannotator.com
hello@geoannotator.com
```

**Avantages** :
- ✅ Professionnel
- ✅ Meilleure délivrabilité
- ✅ Contrôle total

**Configuration** :
1. Mailjet Dashboard → **Account Settings** → **Sender Domains**
2. Ajouter votre domaine : `geoannotator.com`
3. Configurer les enregistrements DNS :
   ```
   SPF:  TXT  v=spf1 include:spf.mailjet.com ~all
   DKIM: TXT  k=rsa; p=<clé fournie par Mailjet>
   ```
4. Attendre validation (24-48h)
5. Mettre à jour `DEFAULT_FROM_EMAIL` sur Render

#### Option B : Sous-domaine Mailjet (Gratuit)
Si vous n'avez pas de domaine :
```
geoannotator@mailjet-custom.com
```

Contactez le support Mailjet pour un sous-domaine gratuit.

---

### 2. Configuration SPF, DKIM, DMARC

Ces enregistrements DNS prouvent que vous êtes autorisé à envoyer des emails.

#### SPF (Sender Policy Framework)
**Ce qui est** : Liste des serveurs autorisés à envoyer pour votre domaine

**Ajouter dans DNS** :
```
Type: TXT
Host: @
Value: v=spf1 include:spf.mailjet.com ~all
```

#### DKIM (DomainKeys Identified Mail)
**Ce qui est** : Signature cryptographique des emails

**Configuration** :
1. Mailjet génère une clé DKIM
2. Ajouter l'enregistrement TXT fourni dans votre DNS
3. Mailjet signe automatiquement tous les emails

#### DMARC (Domain-based Message Authentication)
**Ce qui est** : Politique d'authentification + reporting

**Ajouter dans DNS** :
```
Type: TXT
Host: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

**Vérification** :
```bash
# Tester SPF
nslookup -type=txt yourdomain.com

# Tester DKIM
nslookup -type=txt mailjet._domainkey.yourdomain.com

# Tester DMARC
nslookup -type=txt _dmarc.yourdomain.com
```

---

### 3. Mailjet Reputation Score

**Vérifier votre réputation** :
1. Mailjet Dashboard → **Statistics** → **Reputation**
2. Score idéal : > 95%

**Facteurs** :
- ✅ Taux d'ouverture élevé
- ✅ Peu de bounces (emails non délivrés)
- ✅ Peu de spam complaints
- ❌ Envois massifs soudains

**Amélioration** :
- Envoyez régulièrement (pas 0 puis 1000 d'un coup)
- Nettoyez les adresses invalides
- Encouragez les utilisateurs à ajouter votre adresse aux contacts

---

### 4. Contenu des Emails

**Évitez** :
- ❌ TOUT EN MAJUSCULES
- ❌ Trop de points d'exclamation !!!
- ❌ Mots spam : "Urgent", "Gratuit", "Cliquez ici"
- ❌ Images sans texte
- ❌ Liens raccourcis (bit.ly, etc.)

**Favorisez** :
- ✅ Texte clair et professionnel
- ✅ Ratio texte/HTML équilibré
- ✅ Liens complets (https://geo-annotator.vercel.app/...)
- ✅ Signature identifiable

**Vos emails actuels** : ✅ Conformes (bon contenu)

---

### 5. Liste Blanche Utilisateur

Demandez aux utilisateurs d'ajouter votre adresse email à leurs contacts :

**Message UI** (à ajouter dans le frontend après inscription) :
```
✉️ Pour garantir la réception de nos emails :
1. Vérifiez votre dossier spam
2. Ajoutez noreply@geoannotator.com à vos contacts
3. Marquez l'email comme "Non spam" si nécessaire
```

---

## 📊 Monitoring Mailjet

### Dashboard à surveiller

**Statistics → Messages** :
- Delivered : > 95%
- Opened : ~20-30% (normal pour emails transactionnels)
- Bounced : < 2%
- Spam : < 0.1%

**Si taux spam élevé** :
1. Vérifier SPF/DKIM/DMARC
2. Vérifier domaine d'envoi
3. Améliorer contenu email
4. Contacter support Mailjet

---

## 🚀 Actions Immédiates

### Court Terme (Maintenant)
- [x] Ajouter message "Vérifier spam" dans emails
- [ ] Configurer `FRONTEND_URL` sur Render
- [ ] Vérifier adresse d'envoi dans Mailjet

### Moyen Terme (Cette Semaine)
- [ ] Acquérir domaine propre (geoannotator.com)
- [ ] Configurer SPF/DKIM/DMARC
- [ ] Changer `DEFAULT_FROM_EMAIL` vers domaine propre

### Long Terme (Ce Mois)
- [ ] Monitorer statistiques Mailjet
- [ ] Ajuster contenu si taux spam élevé
- [ ] Ajouter message UI "Ajouter aux contacts"

---

## 🛠️ Configuration Render

**Variables à configurer** :

```bash
# Email
DEFAULT_FROM_EMAIL=noreply@geoannotator.com  # Votre domaine vérifié
DEFAULT_FROM_NAME=GeoAnnotator

# Frontend (pour liens)
FRONTEND_URL=https://geo-annotator.vercel.app  # ⚠️ IMPORTANT !
```

**Vérification** :
1. Render → Service → Environment
2. Vérifier que `FRONTEND_URL` = URL Vercel
3. Sauvegarder → Redéployer

---

## 📧 Test de Délivrabilité

### Mail-Tester
```bash
# Envoyer un email de test à :
test-xxxxx@mail-tester.com

# Score idéal : 10/10
# Vérifie : SPF, DKIM, DMARC, spam score, blacklist
```

### Google Postmaster Tools
```
https://postmaster.google.com/

# Monitore :
- Réputation domaine
- Spam rate
- Authentification
```

---

## ⚠️ Pourquoi les Emails Vont en Spam ?

1. **Domaine Gmail dans FROM** (problème actuel)
   - Gmail.com n'autorise pas Mailjet à envoyer en son nom
   - SPF fail → spam

2. **Pas de DKIM**
   - Email non signé → suspect

3. **Nouveau domaine**
   - Mailjet récent → pas encore de réputation

4. **Contenu générique**
   - "Confirm email" → spam classique

---

## ✅ Solution Complète (Recommandée)

```
1. Acheter domaine : geoannotator.com (~12€/an)
   └─ Namecheap, Gandi, OVH

2. Configurer DNS :
   - SPF :  v=spf1 include:spf.mailjet.com ~all
   - DKIM : <clé Mailjet>
   - DMARC: v=DMARC1; p=quarantine

3. Vérifier domaine dans Mailjet
   └─ 24-48h pour validation

4. Mettre à jour Render :
   DEFAULT_FROM_EMAIL=noreply@geoannotator.com
   FRONTEND_URL=https://geo-annotator.vercel.app

5. Tester avec mail-tester.com
   └─ Objectif : 10/10
```

**Coût** : 12€/an (domaine uniquement)
**Résultat** : 95%+ délivrabilité inbox

---

## 📚 Ressources

- **Mailjet Best Practices** : https://dev.mailjet.com/email/guides/best-practices/
- **SPF Checker** : https://mxtoolbox.com/spf.aspx
- **DKIM Checker** : https://mxtoolbox.com/dkim.aspx
- **Mail Tester** : https://www.mail-tester.com/
- **Google Postmaster** : https://postmaster.google.com/

---

Last updated: 2025-11-18
