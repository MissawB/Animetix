# Admin Financial Dashboard & Ad Equalizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a comprehensive Admin Financial Dashboard to track AI costs, ad event revenues, and donations, featuring an interactive slider simulation to calculate break-even targets.

**Architecture:** We will create an `AdEvent` model to persist impressions/clicks, build REST endpoints for event logging and dashboard aggregation, integrate logging hooks in React components, and build a simulator UI with real-time target calculations.

**Tech Stack:** Django, Django REST Framework, React (Vite + TypeScript), Tailwind CSS, Lucide icons, Pytest.

---

### Task 1: Database Model Changes (Django)

**Files:**
- Modify: `backend/api/animetix/models.py:230-233`
- Run: Django commands to generate and run migrations.

- [ ] **Step 1: Add the `AdEvent` model to `models.py`**
Add the following model class to `backend/api/animetix/models.py`:
```python
class AdEvent(models.Model):
    EVENT_TYPES = [('impression', 'Impression'), ('click', 'Click')]
    AD_TYPES = [('video', 'Video'), ('banner', 'Banner')]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ad_type = models.CharField(max_length=20, choices=AD_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ad_type} {self.event_type} at {self.created_at}"
```

- [ ] **Step 2: Generate migrations**
Run the migration generator in the workspace root:
```bash
python backend/api/manage.py makemigrations animetix
```
Expected output: Migration file generated (e.g. `0013_adevent.py` or similar).

- [ ] **Step 3: Run migrations**
Apply the migration to the database:
```bash
python backend/api/manage.py migrate
```
Expected output: Migration successfully applied.

---

### Task 2: Implement Ad Event Logging API & Tests

**Files:**
- Modify: `backend/api/animetix/api/admin_api.py` (Add AdEvent logging view)
- Modify: `backend/api/animetix/urls/api.py` (Register the path)
- Create: `tests/backend/test_admin_financials.py` (Tests for AdEvent logging)

- [ ] **Step 1: Write the failing test for logging an ad event**
Create `tests/backend/test_admin_financials.py` with the following test code:
```python
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from animetix.models import AdEvent, AITokenUsage, Profile

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_log_ad_event_success(api_client):
    res = api_client.post("/api/v1/billing/log_ad_event/", {
        "event_type": "impression",
        "ad_type": "banner"
    }, format="json")
    assert res.status_code == 201
    assert AdEvent.objects.count() == 1
    event = AdEvent.objects.first()
    assert event.event_type == "impression"
    assert event.ad_type == "banner"

@pytest.mark.django_db
def test_log_ad_event_invalid(api_client):
    res = api_client.post("/api/v1/billing/log_ad_event/", {
        "event_type": "invalid_event",
        "ad_type": "banner"
    }, format="json")
    assert res.status_code == 400
```

- [ ] **Step 2: Run pytest to verify it fails**
Run the command:
```bash
pytest tests/backend/test_admin_financials.py -v
```
Expected: FAIL (No URL matches /api/v1/billing/log_ad_event/)

- [ ] **Step 3: Implement the `AdEventLoggingView` in `backend/api/animetix/api/admin_api.py`**
Import `AdEvent` in `admin_api.py` and implement the APIView:
```python
from rest_framework.response import Response
from ..models import DataCurationTicket, AITokenUsage, AdEvent

class AdEventLoggingAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        event_type = request.data.get("event_type")
        ad_type = request.data.get("ad_type")
        
        valid_events = dict(AdEvent.EVENT_TYPES)
        valid_ads = dict(AdEvent.AD_TYPES)
        
        if event_type not in valid_events or ad_type not in valid_ads:
            return Response({"error": "Invalid event_type or ad_type"}, status=status.HTTP_400_BAD_REQUEST)
            
        event = AdEvent.objects.create(
            event_type=event_type,
            ad_type=ad_type
        )
        return Response({"status": "logged", "id": event.id}, status=status.HTTP_201_CREATED)
```

- [ ] **Step 4: Register route in `backend/api/animetix/urls/api.py`**
Add the path:
```python
    path('billing/log_ad_event/', api_views.AdEventLoggingAPIView.as_view(), name='api_log_ad_event'),
```

- [ ] **Step 5: Run tests to verify they pass**
Run the command:
```bash
pytest tests/backend/test_admin_financials.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**
```bash
git add backend/api/animetix/models.py backend/api/animetix/api/admin_api.py backend/api/animetix/urls/api.py tests/backend/test_admin_financials.py
git commit -m "feat: add AdEvent model and ad event logging API"
```

---

### Task 3: Implement Admin Financials API & Tests

**Files:**
- Modify: `backend/api/animetix/api/admin_api.py` (Add GET view)
- Modify: `backend/api/animetix/urls/api.py` (Register GET path)
- Modify: `tests/backend/test_admin_financials.py` (Add tests for financials GET endpoint)

- [ ] **Step 1: Write tests for GET `/api/v1/admin/financials/`**
Add the following tests to `tests/backend/test_admin_financials.py`:
```python
@pytest.fixture
def admin_client(db, api_client):
    admin_user = User.objects.create_superuser(username="admin", email="admin@animetix.com", password="password")
    api_client.force_authenticate(user=admin_user)
    return admin_user, api_client

@pytest.mark.django_db
def test_admin_financials_permission_denied(api_client):
    # Anonymous client
    res = api_client.get("/api/v1/admin/financials/")
    assert res.status_code == 403

@pytest.mark.django_db
def test_admin_financials_success(admin_client):
    admin, client = admin_client
    
    # Create mock AI usage
    AITokenUsage.objects.create(engine="openai", input_tokens=100, output_tokens=100, total_tokens=200, cost_estimate=1.50)
    AITokenUsage.objects.create(engine="replicate", input_tokens=100, output_tokens=100, total_tokens=200, cost_estimate=2.00)
    
    # Create mock ad events
    AdEvent.objects.create(event_type="impression", ad_type="video")
    AdEvent.objects.create(event_type="impression", ad_type="banner")
    AdEvent.objects.create(event_type="click", ad_type="banner")
    
    # Create mock sponsor profile
    user2 = User.objects.create_user(username="sponsor_user", email="sponsor@test.com")
    profile = user2.profile
    profile.unlocked_badges = ["Sponsor Or"]
    profile.save()
    
    res = client.get("/api/v1/admin/financials/")
    assert res.status_code == 200
    data = res.data
    
    assert data["total_ai_cost"] == 3.50
    assert data["cost_by_engine"]["openai"] == 1.50
    assert data["cost_by_engine"]["replicate"] == 2.00
    assert data["ad_stats"]["video_impressions"] == 1
    assert data["ad_stats"]["banner_impressions"] == 1
    assert data["ad_stats"]["clicks"] == 1
    assert data["donation_stats"]["gold_sponsors"] == 1
    assert data["donation_stats"]["total_donations"] == 5.00
    assert data["estimated_ad_revenue"] == (1 * 0.003) + (1 * 0.001) + (1 * 0.15)
```

- [ ] **Step 2: Run tests to verify they fail**
Run the command:
```bash
pytest tests/backend/test_admin_financials.py -v
```
Expected: FAIL on the financials endpoint tests.

- [ ] **Step 3: Implement the `AdminFinancialsAPIView` in `backend/api/animetix/api/admin_api.py`**
Add the following class to `admin_api.py`:
```python
class AdminFinancialsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # AI cost aggregation
        total_ai_cost = AITokenUsage.objects.aggregate(Sum('cost_estimate'))['cost_estimate__sum'] or 0.0
        
        cost_by_engine = {}
        engine_costs = AITokenUsage.objects.values('engine').annotate(total=Sum('cost_estimate'))
        for item in engine_costs:
            cost_by_engine[item['engine']] = item['total'] or 0.0
            
        # Ad stats aggregation
        video_impressions = AdEvent.objects.filter(ad_type="video", event_type="impression").count()
        banner_impressions = AdEvent.objects.filter(ad_type="banner", event_type="impression").count()
        clicks = AdEvent.objects.filter(event_type="click").count()
        
        # Sponsorship stats (donations)
        gold_sponsors = Profile.objects.filter(unlocked_badges__contains="Sponsor Or").count()
        total_donations = gold_sponsors * 5.00
        
        # Base ad revenue calculation
        # Video CPM: $3.00, Banner CPM: $1.00, CPC: $0.15
        estimated_ad_revenue = (video_impressions * 0.003) + (banner_impressions * 0.001) + (clicks * 0.15)
        
        total_revenue = estimated_ad_revenue + total_donations
        net_margin = total_revenue - total_ai_cost
        
        # Dynamic advice
        if net_margin >= 0:
            recommendation = "Solde positif. L'écosystème est équilibré financièrement."
        else:
            deficit = abs(net_margin)
            needed_video = int(deficit / 0.003)
            needed_clicks = int(deficit / 0.15)
            recommendation = f"Déficit de ${deficit:.2f}. Il est recommandé de générer {needed_video:,} impressions vidéo supplémentaires ou {needed_clicks:,} clics pour équilibrer."
            
        return Response({
            "total_ai_cost": round(total_ai_cost, 4),
            "cost_by_engine": cost_by_engine,
            "ad_stats": {
                "video_impressions": video_impressions,
                "banner_impressions": banner_impressions,
                "clicks": clicks
            },
            "donation_stats": {
                "gold_sponsors": gold_sponsors,
                "total_donations": round(total_donations, 2)
            },
            "estimated_ad_revenue": round(estimated_ad_revenue, 4),
            "total_revenue": round(total_revenue, 4),
            "net_margin": round(net_margin, 4),
            "recommendation": recommendation
        })
```

- [ ] **Step 4: Register route in `backend/api/animetix/urls/api.py`**
Add the path:
```python
    path('admin/financials/', api_views.AdminFinancialsAPIView.as_view(), name='api_admin_financials'),
```

- [ ] **Step 5: Run tests to verify they pass**
Run the command:
```bash
pytest tests/backend/test_admin_financials.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**
```bash
git add backend/api/animetix/api/admin_api.py backend/api/animetix/urls/api.py tests/backend/test_admin_financials.py
git commit -m "feat: add AdminFinancialsAPIView and financials endpoint tests"
```

---

### Task 4: Integrate Ad Logging in Frontend Components

**Files:**
- Modify: `frontend/src/features/billing/components/SimulatedAdBanner.tsx`
- Modify: `frontend/src/features/billing/components/SponsorStreamModal.tsx`

- [ ] **Step 1: Update `SimulatedAdBanner.tsx`**
Inject an api helper or fetch POST request to log impressions and clicks.
Modify `SimulatedAdBanner.tsx` to call `/api/v1/billing/log_ad_event/` inside `useEffect` (for impressions) and `handleCtaClick` (for clicks):
```typescript
  useEffect(() => {
    const random = SPONSORS[Math.floor(Math.random() * SPONSORS.length)];
    setSponsor(random);
    
    // Log Banner Impression
    fetch('/api/v1/billing/log_ad_event/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: 'impression', ad_type: 'banner' })
    }).catch(err => console.error('Failed to log ad impression', err));
  }, []);

  const handleCtaClick = () => {
    // Log Banner Click
    fetch('/api/v1/billing/log_ad_event/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: 'click', ad_type: 'banner' })
    }).catch(err => console.error('Failed to log ad click', err));

    window.open(sponsor.url, '_blank', 'noopener,noreferrer');
  };
```

- [ ] **Step 2: Update `SponsorStreamModal.tsx`**
Modify `startAdPlayback` inside `frontend/src/features/billing/components/SponsorStreamModal.tsx` to log a video ad impression when video playback starts:
```typescript
  const startAdPlayback = () => {
    if (hasError) return;

    try {
      const google = (window as any).google;
      
      if (adDisplayContainerRef.current) {
        adDisplayContainerRef.current.initialize();
      }

      const adsRequest = new google.ima.AdsRequest();
      adsRequest.adTagUrl = AD_TAG_URL;
      
      const width = adContainerRef.current?.clientWidth || 640;
      const height = adContainerRef.current?.clientHeight || 360;
      adsRequest.linearAdSlotWidth = width;
      adsRequest.linearAdSlotHeight = height;
      adsRequest.nonLinearAdSlotWidth = width;
      adsRequest.nonLinearAdSlotHeight = height;

      setIsAdStarted(true);

      // Log Video Ad Impression
      fetch('/api/v1/billing/log_ad_event/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: 'impression', ad_type: 'video' })
      }).catch(err => console.error('Failed to log video ad impression', err));

      adsLoaderRef.current.requestAds(adsRequest);
      // ... rest of the method
```
Also call it if falling back to the local video player. Locate where the fallback video player gets initialized or played (in `hasError` rendering, when video autoPlay starts):
```typescript
  // In SponsorStreamModal.tsx, in the video elements or fallback useEffect
```

- [ ] **Step 3: Commit**
```bash
git add frontend/src/features/billing/components/SimulatedAdBanner.tsx frontend/src/features/billing/components/SponsorStreamModal.tsx
git commit -m "feat: track impressions and clicks in SimulatedAdBanner and SponsorStreamModal"
```

---

### Task 5: Create Financial Dashboard Page (Frontend)

**Files:**
- Create: `frontend/src/pages/admin/FinancialDashboardPage.tsx`

- [ ] **Step 1: Write `FinancialDashboardPage.tsx`**
Create a new file `frontend/src/pages/admin/FinancialDashboardPage.tsx`. Integrate state variables for actual metrics, as well as simulator sliders that compute results instantly.
Include design components matching the manga aesthetic, standard cards, sliders, and color badges.
```tsx
import React, { useState, useEffect } from 'react';
import { Shield, Sparkles, AlertTriangle, Coins, RefreshCw, BarChart2, TrendingUp, HelpCircle } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

interface FinancialData {
  total_ai_cost: number;
  cost_by_engine: Record<string, number>;
  ad_stats: {
    video_impressions: number;
    banner_impressions: number;
    clicks: number;
  };
  donation_stats: {
    gold_sponsors: number;
    total_donations: number;
  };
  estimated_ad_revenue: number;
  total_revenue: number;
  net_margin: number;
  recommendation: string;
}

const FinancialDashboardPage: React.FC = () => {
  const [data, setData] = useState<FinancialData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sliders simulation values
  const [videoCpm, setVideoCpm] = useState<number>(3.00);
  const [bannerCpm, setBannerCpm] = useState<number>(1.00);
  const [cpc, setCpc] = useState<number>(0.15);
  const [donationVal, setDonationVal] = useState<number>(5.00);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/admin/financials/');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px] bg-[#fffcf0] dark:bg-[#1a1a2e]">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto p-8 mt-12 bg-red-500/10 border border-red-500/30 rounded-2xl text-center">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-red-500">Erreur lors de la récupération des données financières</h3>
        <p className="text-gray-400 mt-2">{error}</p>
        <button onClick={fetchData} className="mt-6 px-4 py-2 bg-red-500 text-white rounded-xl font-bold text-xs uppercase">
          Réessayer
        </button>
      </div>
    );
  }

  // Live simulation calculations
  const simAdRevenue = 
    (data.ad_stats.video_impressions * (videoCpm / 1000)) + 
    (data.ad_stats.banner_impressions * (bannerCpm / 1000)) + 
    (data.ad_stats.clicks * cpc);

  const simDonations = data.donation_stats.gold_sponsors * donationVal;
  const simTotalRevenue = simAdRevenue + simDonations;
  const simNetMargin = simTotalRevenue - data.total_ai_cost;

  // Live breakeven calculations
  const isDeficit = simNetMargin < 0;
  const deficitVal = Math.abs(simNetMargin);
  const neededVideoImpressions = videoCpm > 0 ? Math.ceil((deficitVal / (videoCpm / 1000))) : 0;
  const neededClicks = cpc > 0 ? Math.ceil(deficitVal / cpc) : 0;

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] bg-manga-overlay transition-colors duration-500">
        <div className="max-w-7xl mx-auto px-6 py-12">
          
          {/* Header */}
          <div className="mb-12">
            <div className="flex items-center gap-3 text-blue-500 font-black uppercase tracking-widest text-xs mb-3">
              <Shield size={16} /> Dashboard Financier Admin
            </div>
            <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
              EQUILIBRE <span className="text-blue-500">FINANCIER</span>
            </h1>
            <p className="text-gray-500 font-bold uppercase tracking-widest mt-2 text-xs">
              Calculez et équilibrez vos coûts d'IA avec la régie publicitaire
            </p>
          </div>

          {/* KPI Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card padding="md" className="border-2 border-red-500/20 bg-white dark:bg-[#0f0f1a]">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-wider text-gray-500 mb-1">Coût Total IA</p>
                  <h3 className="text-3xl font-black text-red-500">${data.total_ai_cost.toFixed(2)}</h3>
                </div>
                <Coins className="text-red-500 w-5 h-5" />
              </div>
              <p className="text-[10px] text-gray-400 mt-3 font-mono">Consommation cumulée des API</p>
            </Card>

            <Card padding="md" className="border-2 border-green-500/20 bg-white dark:bg-[#0f0f1a]">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-wider text-gray-500 mb-1">Revenus Pubs (Simulés)</p>
                  <h3 className="text-3xl font-black text-green-500">${simAdRevenue.toFixed(2)}</h3>
                </div>
                <TrendingUp className="text-green-500 w-5 h-5" />
              </div>
              <p className="text-[10px] text-gray-400 mt-3 font-mono">
                {data.ad_stats.video_impressions} videos • {data.ad_stats.clicks} clics
              </p>
            </Card>

            <Card padding="md" className="border-2 border-yellow-500/20 bg-white dark:bg-[#0f0f1a]">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-wider text-gray-500 mb-1">Dons (Sponsors Or)</p>
                  <h3 className="text-3xl font-black text-yellow-500">${simDonations.toFixed(2)}</h3>
                </div>
                <Sparkles className="text-yellow-500 w-5 h-5" />
              </div>
              <p className="text-[10px] text-gray-400 mt-3 font-mono">
                {data.donation_stats.gold_sponsors} sponsors or actifs
              </p>
            </Card>

            <Card padding="md" className={`border-2 bg-white dark:bg-[#0f0f1a] ${isDeficit ? 'border-red-500' : 'border-green-500'}`}>
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-wider text-gray-500 mb-1">Solde Net (Simulation)</p>
                  <h3 className={`text-3xl font-black ${isDeficit ? 'text-red-500' : 'text-green-500'}`}>
                    {isDeficit ? '-' : '+'}${deficitVal.toFixed(2)}
                  </h3>
                </div>
                <div className={`px-2 py-0.5 rounded text-[8px] font-black uppercase ${isDeficit ? 'bg-red-500/10 text-red-500 border border-red-500/30' : 'bg-green-500/10 text-green-500 border border-green-500/30'}`}>
                  {isDeficit ? 'Déficit' : 'Bénéfice'}
                </div>
              </div>
              <p className="text-[10px] text-gray-400 mt-3 font-mono">Total revenus - Coûts IA</p>
            </Card>
          </div>

          {/* Interactive Equalizer Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            {/* Sliders Console */}
            <div className="lg:col-span-2 space-y-6">
              <Card padding="lg" className="bg-white dark:bg-[#0f0f1a]">
                <h3 className="text-xl font-black italic uppercase text-black dark:text-white mb-6 flex items-center gap-2">
                  <BarChart2 className="w-5 h-5 text-blue-500" /> CONSOLE D'ÉGALISATION INTERACTIVE
                </h3>
                
                <div className="space-y-6">
                  {/* Slider 1: Video CPM */}
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                      <span>CPM Vidéo (pour 1000 vues)</span>
                      <span className="text-blue-500 font-mono">${videoCpm.toFixed(2)}</span>
                    </div>
                    <input 
                      type="range" min="0.50" max="15.00" step="0.10" value={videoCpm} 
                      onChange={(e) => setVideoCpm(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                    />
                  </div>

                  {/* Slider 2: Banner CPM */}
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                      <span>CPM Bannière (pour 1000 vues)</span>
                      <span className="text-blue-500 font-mono">${bannerCpm.toFixed(2)}</span>
                    </div>
                    <input 
                      type="range" min="0.10" max="5.00" step="0.10" value={bannerCpm} 
                      onChange={(e) => setBannerCpm(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                    />
                  </div>

                  {/* Slider 3: CPC */}
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                      <span>CPC (Revenu par clic pub)</span>
                      <span className="text-blue-500 font-mono">${cpc.toFixed(2)}</span>
                    </div>
                    <input 
                      type="range" min="0.05" max="2.00" step="0.05" value={cpc} 
                      onChange={(e) => setCpc(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                    />
                  </div>

                  {/* Slider 4: Donation Value */}
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                      <span>Valeur Don Unique (Sponsor Or)</span>
                      <span className="text-blue-500 font-mono">${donationVal.toFixed(2)}</span>
                    </div>
                    <input 
                      type="range" min="1.00" max="30.00" step="0.50" value={donationVal} 
                      onChange={(e) => setDonationVal(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500" 
                    />
                  </div>
                </div>
              </Card>
            </div>

            {/* Break-even & Recommendations */}
            <div className="space-y-6">
              <Card padding="lg" className="bg-[#0b0c15] text-white border border-blue-500/20">
                <h3 className="text-md font-black italic uppercase text-yellow-500 mb-4 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4" /> SEUIL DE RENTABILITÉ
                </h3>

                {isDeficit ? (
                  <div className="space-y-4">
                    <p className="text-xs text-gray-300 leading-relaxed font-mono">
                      Pour compenser le déficit simulé de <span className="text-red-500 font-bold">${deficitVal.toFixed(2)}</span> avec les taux sélectionnés, le site doit générer au choix :
                    </p>
                    <div className="bg-black/40 p-4 rounded-xl border border-white/5 space-y-3 font-mono">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">Vues Vidéo Recom. :</span>
                        <span className="text-yellow-400 font-bold">{neededVideoImpressions.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-400">OU Clics Pubs :</span>
                        <span className="text-yellow-400 font-bold">{neededClicks.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-green-500/10 border border-green-500/30 p-4 rounded-xl text-green-400 text-xs leading-relaxed font-mono">
                    Félicitations ! Les paramètres actuels permettent de dégager un bénéfice de <span className="font-bold">${deficitVal.toFixed(2)}</span>. Aucun trafic publicitaire supplémentaire n'est nécessaire pour combler les coûts.
                  </div>
                )}
              </Card>

              <Card padding="lg" className="bg-white dark:bg-[#0f0f1a]">
                <h3 className="text-md font-black italic uppercase text-blue-500 mb-4 flex items-center gap-1.5">
                  <HelpCircle className="w-4 h-4" /> RECOMMANDATION GLOBALE
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed font-mono bg-gray-50 dark:bg-black/30 p-4 rounded-xl border border-gray-100 dark:border-white/5">
                  {data.recommendation}
                </p>
              </Card>
            </div>
          </div>

          {/* Engine Breakdown */}
          <Card padding="lg" className="bg-white dark:bg-[#0f0f1a]">
            <h3 className="text-lg font-black italic uppercase text-black dark:text-white mb-6">
              RÉPARTITION DES COÛTS PAR MOTEUR D'IA
            </h3>
            <div className="space-y-4">
              {Object.entries(data.cost_by_engine).length === 0 ? (
                <p className="text-xs text-gray-500">Aucun coût d'IA enregistré.</p>
              ) : (
                Object.entries(data.cost_by_engine).map(([engine, cost]) => {
                  const percentage = data.total_ai_cost > 0 ? (cost / data.total_ai_cost) * 100 : 0;
                  return (
                    <div key={engine} className="space-y-1 font-mono">
                      <div className="flex justify-between text-xs">
                        <span className="text-black dark:text-white font-bold uppercase">{engine}</span>
                        <span className="text-gray-500">${cost.toFixed(2)} ({percentage.toFixed(1)}%)</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                        <div className="bg-blue-500 h-full" style={{ width: `${percentage}%` }} />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </Card>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default FinancialDashboardPage;
```

---

### Task 6: Register Route & Add Navigation Links

**Files:**
- Modify: `frontend/src/features/admin/routes/AdminRoutes.tsx`
- Modify: `frontend/src/pages/admin/AdminDashboardPage.tsx`

- [ ] **Step 1: Register Route in `AdminRoutes.tsx`**
Import `FinancialDashboardPage` and add the route path `/admin/financials/`:
```typescript
const FinancialDashboardPage = lazy(() => import('../../../pages/admin/FinancialDashboardPage'));

// inside AdminRoutes = ( ... )
<Route path="/admin/financials/" element={<FinancialDashboardPage />} />
```

- [ ] **Step 2: Add Link to `AdminDashboardPage.tsx`**
Add the card to the list of `adminModules` in `AdminDashboardPage.tsx`:
```typescript
    {
      title: 'Financial Dashboard',
      desc: 'Calculer les coûts IA et égaliser avec les pubs/dons.',
      icon: <Coins className="w-8 h-8 text-yellow-500" />,
      path: '/admin/financials/',
      color: 'yellow'
    }
```
Import `Coins` from `lucide-react` at the top of the file if not already imported.

---

### Task 7: Full Verification & E2E Validation

**Files:**
- Run: Manual check to verify routing and simulation.
- Run: Check network calls when playing/clicking ads.

- [ ] **Step 1: Run Django Server locally**
Make sure server is running and database is fully migrated.

- [ ] **Step 2: Access the page**
Visit `/admin/financials/` in the browser, test moving all sliders, and verify cost breakdown.
