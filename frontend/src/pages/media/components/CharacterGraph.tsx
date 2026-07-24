import React, { Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Maximize2, Minimize2, LocateFixed, ZoomIn, ZoomOut } from 'lucide-react';
import { useCharacterGraph } from '../../../features/media/hooks/useCharacterGraph';

// ~200 Ko : chargé uniquement quand la vue Graphe est ouverte
import ForceGraph2D, {
  type ForceGraphMethods,
  type NodeObject,
  type LinkObject,
} from '../../../components/LazyForceGraph2D';

const INK = '#0B0C10';
const PAPER = 'rgba(244, 241, 232, 0.9)';
const GOLD = '#FDB913';
const SHU = '#E8442B';

const CONTROL_BTN =
  'flex h-9 w-9 items-center justify-center rounded-full border border-[#F4F1E8]/15 bg-[#0B0C10]/80 text-[#8F94A5] backdrop-blur transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]';

interface CharacterGraphProps {
  mediaType?: string;
  itemId?: string;
}

export const CharacterGraph: React.FC<CharacterGraphProps> = ({ mediaType, itemId }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data, isLoading, isError } = useCharacterGraph(mediaType, itemId);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const fgRef = React.useRef<ForceGraphMethods | null>(null);
  const didFitRef = React.useRef(false);
  const [size, setSize] = React.useState({ width: 0, height: 480 });
  const [expanded, setExpanded] = React.useState(false);
  const [hovering, setHovering] = React.useState(false);
  // lu à chaque frame par les rendus canvas — jamais via l'état React
  const hoverRef = React.useRef<string | null>(null);
  // cache des portraits ; le canvas repeint en continu, les images
  // apparaissent d'elles-mêmes dès qu'elles sont chargées
  const imgCache = React.useRef(new Map<string, HTMLImageElement>());
  const reducedMotion = React.useMemo(
    () =>
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  );

  React.useEffect(() => {
    if (!data) return;
    for (const n of data.nodes) {
      if (!n.image || imgCache.current.has(n.image)) continue;
      const img = new Image();
      imgCache.current.set(n.image, img);
      img.src = n.image;
    }
  }, [data]);

  React.useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) =>
      setSize({
        width: entries[0].contentRect.width,
        height: entries[0].contentRect.height,
      }),
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const { graphData, hiddenCount } = React.useMemo(() => {
    if (!data) return { graphData: { nodes: [], links: [] }, hiddenCount: 0 };
    const linked = new Set(data.links.flatMap((l) => [l.source, l.target]));
    // un 相関図 ne montre que les personnages reliés ; les isolés (aucune
    // relation connue) ne feraient que dériver en périphérie
    const nodes = data.nodes.filter((n) => linked.has(n.id));
    const maxPop = Math.max(1, ...nodes.map((n) => n.popularity));
    return {
      graphData: {
        nodes: nodes.map((n) => ({
          ...n,
          // rayon 6-16 selon la popularité (échelle racine pour écraser la tête)
          __r: 6 + 10 * Math.sqrt(n.popularity / maxPop),
        })),
        links: data.links.map((l) => ({ ...l })),
      },
      hiddenCount: data.nodes.length - nodes.length,
    };
  }, [data]);

  const recenter = React.useCallback(() => {
    const fg = fgRef.current;
    if (!fg) return;
    const fitMs = reducedMotion ? 0 : 400;
    fg.zoomToFit(fitMs, 48);
    // même plancher que le cadrage initial : les chaînes périphériques
    // étirent la bbox et rendraient les médaillons illisibles
    window.setTimeout(() => {
      if (fg.zoom() < 1.2) fg.zoom(1.2, reducedMotion ? 0 : 300);
    }, fitMs + 20);
  }, [reducedMotion]);

  const zoomBy = React.useCallback((factor: number) => {
    const fg = fgRef.current;
    if (fg) fg.zoom(fg.zoom() * factor, 300);
  }, []);

  // ---- rendus canvas : identités stables, aucun re-render React par frame ----

  const lerpFactor = reducedMotion ? 1 : 0.25;

  const paintNode = React.useCallback(
    (
      node: NodeObject & Record<string, unknown>,
      ctx: CanvasRenderingContext2D,
      globalScale: number,
    ) => {
      // facteur de survol lissé (0 -> 1) : tout en découle en fondu
      const target = node.id === hoverRef.current ? 1 : 0;
      node.__h = ((node.__h as number) ?? 0) + (target - ((node.__h as number) ?? 0)) * lerpFactor;
      const h = node.__h as number;
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      const r = ((node.__r as number) ?? 10) * (1 + 0.16 * h);
      const img = node.image ? imgCache.current.get(node.image as string) : undefined;
      const drawable = !!img && img.complete && img.naturalWidth > 0;

      // médaillon : portrait découpé en cercle, sinon initiale sur encre
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.closePath();
      if (drawable) {
        ctx.clip();
        const side = Math.min(img.naturalWidth, img.naturalHeight);
        const sx = (img.naturalWidth - side) / 2;
        const sy = (img.naturalHeight - side) / 2;
        ctx.drawImage(img, sx, sy, side, side, x - r, y - r, r * 2, r * 2);
        // voile d'encre qui se lève au survol
        ctx.fillStyle = `rgba(11, 12, 16, ${0.18 * (1 - h)})`;
        ctx.fill();
      } else {
        ctx.fillStyle = '#0F1016';
        ctx.fill();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = GOLD;
        ctx.font = `700 ${Math.max(r, 6)}px Montserrat, sans-serif`;
        ctx.fillText((node.name as string).charAt(0), x, y);
      }
      ctx.restore();

      // anneau or, doublé d'un anneau vermillon qui apparaît en fondu
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.lineWidth = (1.5 + 1.5 * h) / globalScale;
      ctx.strokeStyle = GOLD;
      ctx.stroke();
      if (h > 0.02) {
        ctx.beginPath();
        ctx.arc(x, y, r, 0, 2 * Math.PI);
        ctx.globalAlpha = h;
        ctx.strokeStyle = SHU;
        ctx.stroke();
        ctx.globalAlpha = 1;
      }

      // nom : fondu au survol, permanent pour les têtes d'affiche / au zoom
      const staticLabel = globalScale > 1.4 || ((node.__r as number) ?? 0) > 12;
      const labelAlpha = staticLabel ? 1 : h;
      if (labelAlpha > 0.03) {
        const fontSize = Math.max(11 / globalScale, 3);
        ctx.globalAlpha = labelAlpha;
        ctx.font = `${h > 0.5 ? 800 : 600} ${fontSize}px Inter, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        const ly = y + r + 3 / globalScale;
        ctx.lineWidth = 3 / globalScale;
        ctx.strokeStyle = 'rgba(11, 12, 16, 0.9)';
        ctx.strokeText(node.name as string, x, ly);
        ctx.fillStyle = h > 0.5 ? GOLD : PAPER;
        ctx.fillText(node.name as string, x, ly);
        ctx.globalAlpha = 1;
      }
    },
    [lerpFactor],
  );

  const paintLink = React.useCallback(
    (link: LinkObject & Record<string, unknown>, ctx: CanvasRenderingContext2D) => {
      const s = link.source as (NodeObject & Record<string, unknown>) | undefined;
      const t2 = link.target as (NodeObject & Record<string, unknown>) | undefined;
      if (!s || !t2 || typeof s !== 'object' || typeof t2 !== 'object') return;
      const hov = hoverRef.current;
      const hot = hov != null && (s.id === hov || t2.id === hov);
      // halo progressif : papier -> or selon le facteur de survol lissé
      link.__h =
        ((link.__h as number) ?? 0) + ((hot ? 1 : 0) - ((link.__h as number) ?? 0)) * lerpFactor;
      const h = link.__h as number;
      ctx.beginPath();
      ctx.moveTo(s.x ?? 0, s.y ?? 0);
      ctx.lineTo(t2.x ?? 0, t2.y ?? 0);
      ctx.strokeStyle = `rgba(${244 + 9 * h}, ${241 - 56 * h}, ${232 - 213 * h}, ${
        0.16 + 0.55 * h
      })`;
      ctx.lineWidth = 1.1 + 1.1 * h;
      ctx.stroke();
    },
    [lerpFactor],
  );

  const paintPointerArea = React.useCallback(
    (node: NodeObject & Record<string, unknown>, color: string, ctx: CanvasRenderingContext2D) => {
      ctx.beginPath();
      ctx.arc(node.x ?? 0, node.y ?? 0, ((node.__r as number) ?? 0) + 4, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
    },
    [],
  );

  const onNodeHover = React.useCallback((node: NodeObject | null) => {
    hoverRef.current = node ? (node.id as string) : null;
    setHovering(!!node);
  }, []);

  const onNodeClick = React.useCallback(
    (node: NodeObject) => navigate(`/media/Character/${node.id}/`),
    [navigate],
  );

  const onEngineStop = React.useCallback(() => {
    // cadre le graphe une seule fois, pas après chaque drag
    if (!didFitRef.current) {
      didFitRef.current = true;
      const fg = fgRef.current;
      if (!fg) return;
      fg.zoomToFit(0, 40);
      if (fg.zoom() < 1.2) fg.zoom(1.2, 400);
    }
  }, []);

  if (isLoading)
    return (
      <div className="flex h-[480px] items-center justify-center rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] text-sm text-[#8F94A5]">
        {t('media.detail.graph_loading', 'Construction du graphe…')}
      </div>
    );

  if (isError || graphData.nodes.length === 0)
    return (
      <div className="flex h-[480px] items-center justify-center rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] text-sm text-[#8F94A5]">
        {t('media.detail.graph_empty', 'Pas assez de données de relations pour cette œuvre.')}
      </div>
    );

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] ${
        expanded ? 'h-[75vh]' : 'h-[480px]'
      } ${hovering ? 'cursor-pointer' : ''}`}
    >
      <p className="pointer-events-none absolute left-4 top-3 z-10 text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
        {t(
          'media.detail.graph_hint',
          'Taille = popularité · trait = relation · clic = ouvrir la fiche',
        )}
      </p>

      {/* Commandes : zoom, recentrage, agrandissement */}
      <div className="absolute right-3 top-3 z-10 flex flex-col gap-2">
        <button
          type="button"
          onClick={() => {
            setExpanded((e) => !e);
            window.setTimeout(() => recenter(), 60);
          }}
          aria-label={
            expanded
              ? t('media.detail.graph_shrink', 'Réduire le graphe')
              : t('media.detail.graph_expand', 'Agrandir le graphe')
          }
          className={CONTROL_BTN}
        >
          {expanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </button>
        <button
          type="button"
          onClick={() => zoomBy(1.5)}
          aria-label={t('media.detail.graph_zoom_in', 'Zoomer')}
          className={CONTROL_BTN}
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => zoomBy(1 / 1.5)}
          aria-label={t('media.detail.graph_zoom_out', 'Dézoomer')}
          className={CONTROL_BTN}
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={recenter}
          aria-label={t('media.detail.graph_recenter', 'Recentrer le graphe')}
          className={CONTROL_BTN}
        >
          <LocateFixed className="h-4 w-4" />
        </button>
      </div>

      <Suspense
        fallback={
          <div className="flex h-full items-center justify-center text-sm text-[#8F94A5]">
            {t('media.detail.graph_loading', 'Construction du graphe…')}
          </div>
        }
      >
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          width={size.width || undefined}
          height={size.height}
          backgroundColor={INK}
          onEngineStop={onEngineStop}
          nodeVal={(n: NodeObject) => (n as Record<string, unknown>).__r as number}
          nodeLabel={() => ''}
          linkCanvasObjectMode={() => 'replace'}
          linkCanvasObject={paintLink}
          onNodeClick={onNodeClick}
          onNodeHover={onNodeHover}
          nodeCanvasObject={paintNode}
          nodePointerAreaPaint={paintPointerArea}
          linkDirectionalParticles={0}
          cooldownTicks={120}
          nodeRelSize={1}
        />
      </Suspense>
      {hiddenCount > 0 && (
        <p className="pointer-events-none absolute bottom-3 left-4 z-10 text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
          {t('media.detail.graph_hidden', '{{count}} personnages sans relation connue masqués', {
            count: hiddenCount,
          })}
        </p>
      )}
      <span
        className="pointer-events-none absolute bottom-3 right-4 z-10 text-[9px] font-black uppercase tracking-[0.25em] text-[#E8442B]/70"
        aria-hidden
      >
        相関図
      </span>
    </div>
  );
};
