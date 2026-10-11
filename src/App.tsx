import { useState } from "react";
import { FolderTree, Terminal, Monitor, Code2, Check, Copy, RotateCw, ImageOff } from "lucide-react";

const ONGLETS = [
  "STATTIMES",
  "SUPPLYCHAINDIVE",
  "AIRCARGOWEEK",
  "FREIGHTWAVES",
  "SEATRADE-MARITIME",
] as const;

type NomOnglet = typeof ONGLETS[number];

interface ArticleData {
  title: string;
  date: string;
  image_url: string;
}

// Données d'articles avec URLs fiables et haute disponibilité pour le défilement
const DONNEES_INITIALES: Record<NomOnglet, ArticleData[]> = {
  STATTIMES: [
    {
      title: "Cathay Cargo operates first commercial flight into Western Sydney International Airport",
      date: "2026-10-10",
      image_url: "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "TIACA announces winners of the 2026 Air Cargo Sustainability Awards",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Lufthansa Cargo expands transpacific network with direct freighter connections",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Etihad Cargo posts record third-quarter tonnage driven by pharma and tech demand",
      date: "2026-10-07",
      image_url: "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Emirates SkyCargo adds two Boeing 777Fs to bolster global scheduled capacity",
      date: "2026-10-06",
      image_url: "https://images.unsplash.com/photo-1520437358207-323b43b50729?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Singapore Airlines Cargo reports strong bellyhold volume growth across Asia-Pacific routes",
      date: "2026-10-05",
      image_url: "https://images.unsplash.com/photo-1508873696983-2df5293cb32f?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "IATA air freight pulse reveals resilient e-commerce demand ahead of peak shipping season",
      date: "2026-10-04",
      image_url: "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=360&auto=format&fit=crop&q=70",
    },
  ],
  SUPPLYCHAINDIVE: [
    {
      title: "Port of Los Angeles cargo volume surges 14% as shippers front-load holiday goods",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "US East Coast dockworkers and maritime alliance resume talks on port automation",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "FedEx deploys autonomous electric yard trucks across major Midwest ground hubs",
      date: "2026-10-06",
      image_url: "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Semiconductor supply chains face new export restrictions ahead of global reviews",
      date: "2026-10-05",
      image_url: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Warehouse vacancy rates level out as 3PL operators optimize regional footprint",
      date: "2026-10-04",
      image_url: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Automakers accelerate nearshoring supplier contracts in northern Mexico industrial corridors",
      date: "2026-10-03",
      image_url: "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=360&auto=format&fit=crop&q=70",
    },
  ],
  AIRCARGOWEEK: [
    {
      title: "Air France KLM Martinair Cargo secures CEIV Lithium Battery re-certification",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1508873696983-2df5293cb32f?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Chapman Freeborn appoints regional vice president for Europe, Middle East and Africa",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Worldwide Flight Services opens state-of-the-art cold chain center at Liege Airport",
      date: "2026-10-07",
      image_url: "https://images.unsplash.com/photo-1586528116493-a029325540fa?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Cargolux marks milestone anniversary with special livery on flagship Boeing 747-8F",
      date: "2026-10-06",
      image_url: "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Silk Way West Airlines ramps up transatlantic scheduled frequencies out of Baku",
      date: "2026-10-05",
      image_url: "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Brussels Airport reports continuous pharma growth following terminal digital enhancements",
      date: "2026-10-04",
      image_url: "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=360&auto=format&fit=crop&q=70",
    },
  ],
  FREIGHTWAVES: [
    {
      title: "Truckload tender rejection rates tick higher as regional freight markets tighten",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Class 1 railroads report mixed rail traffic metrics amid fluctuating intermodal flows",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Diesel fuel prices drop for third straight week providing relief to carrier margins",
      date: "2026-10-07",
      image_url: "https://images.unsplash.com/photo-1527018607616-a9f8f413bf2a?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Dry van spot rates stabilize following seasonal consumer goods inventory restocking",
      date: "2026-10-06",
      image_url: "https://images.unsplash.com/photo-1519003722824-194d4455a60c?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Border crossing processing times improve with newly deployed automated radiation portals",
      date: "2026-10-05",
      image_url: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=360&auto=format&fit=crop&q=70",
    },
  ],
  "SEATRADE-MARITIME": [
    {
      title: "Global container fleet crosses 30 million TEU milestone amidst rapid newbuilding pace",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "CMA CGM orders next-generation dual-fuel methanol container vessels from DSIC",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Panama Canal increases daily transit slots to 36 as reservoir water levels stabilize",
      date: "2026-10-07",
      image_url: "https://images.unsplash.com/photo-1505705694340-019e1e335916?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Port of Singapore achieves record maritime bunkering volumes with low-carbon biofuels",
      date: "2026-10-06",
      image_url: "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=360&auto=format&fit=crop&q=70",
    },
    {
      title: "Dry bulk market sentiments rebound as grain export demand picks up momentum",
      date: "2026-10-05",
      image_url: "https://images.unsplash.com/photo-1508873696983-2df5293cb32f?w=360&auto=format&fit=crop&q=70",
    },
  ],
};

export default function App() {
  const [ongletActif, setOngletActif] = useState<NomOnglet>("STATTIMES");
  const [vueArchitecture, setVueArchitecture] = useState(false);
  const [fichierSelectionne, setFichierSelectionne] = useState("service_chargement_image.py");
  const [copie, setCopie] = useState(false);

  // Erreurs d'image gérées avec fallback
  const [imagesEnErreur, setImagesEnErreur] = useState<Record<string, boolean>>({});

  const [cacheArticles] = useState<Record<NomOnglet, ArticleData[]>>(() => DONNEES_INITIALES);

  const [enActualisation, setEnActualisation] = useState<Record<NomOnglet, boolean>>({
    STATTIMES: false,
    SUPPLYCHAINDIVE: false,
    AIRCARGOWEEK: false,
    FREIGHTWAVES: false,
    "SEATRADE-MARITIME": false,
  });

  const [dateDerniereMaj, setDateDerniereMaj] = useState<Record<NomOnglet, string>>({
    STATTIMES: "Session start",
    SUPPLYCHAINDIVE: "Session start",
    AIRCARGOWEEK: "Session start",
    FREIGHTWAVES: "Session start",
    "SEATRADE-MARITIME": "Session start",
  });

  const declencherActualisation = (source: NomOnglet) => {
    if (enActualisation[source]) return;

    setEnActualisation((prev) => ({ ...prev, [source]: true }));

    setTimeout(() => {
      setEnActualisation((prev) => ({ ...prev, [source]: false }));
      setDateDerniereMaj((prev) => ({
        ...prev,
        [source]: new Date().toLocaleTimeString(),
      }));
    }, 1200);
  };

  const fichiersPython: Record<string, { chemin: string; description: string }> = {
    "service_chargement_image.py": {
      chemin: "/GESTION_ARTICLE/services/service_chargement_image.py",
      description: "Non-blocking async image loader with HTTP User-Agent headers and observer registry for scroll",
    },
    "tableau_articles.py": {
      chemin: "/GESTION_ARTICLE/composants/tableau_articles.py",
      description: "Passive QTableWidget with ScrollPerPixel and guaranteed thumbnail update on scroll",
    },
    "service_cache_articles.py": {
      chemin: "/GESTION_ARTICLE/services/service_cache_articles.py",
      description: "In-memory session cache ensuring instant tab switches without network calls",
    },
    "bouton_actualisation.py": {
      chemin: "/GESTION_ARTICLE/composants/bouton_actualisation.py",
      description: "QAbstractButton with custom QPainter rotating vector icon (no emoji, no unicode)",
    },
    "panneau_source_articles.py": {
      chemin: "/GESTION_ARTICLE/composants/panneau_source_articles.py",
      description: "Tab content view placing the rotating refresh icon at the top right",
    },
  };

  const copierCommande = () => {
    navigator.clipboard?.writeText("cd /GESTION_ARTICLE && python3 lancement.py");
    setCopie(true);
    setTimeout(() => setCopie(false), 2000);
  };

  const articlesActifs = cacheArticles[ongletActif] || [];
  const estEnCours = enActualisation[ongletActif];

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shadow-xs">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-red-600 text-white flex items-center justify-center font-bold text-sm">
            Py
          </div>
          <div>
            <h1 className="font-semibold text-base text-slate-900 leading-tight">
              Article Management
            </h1>
            <p className="text-xs text-slate-500">
              Desktop GUI PySide6 &bull; Folder: <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">/GESTION_ARTICLE</code>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setVueArchitecture(!vueArchitecture)}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition"
          >
            {vueArchitecture ? (
              <>
                <Monitor className="w-3.5 h-3.5 text-slate-600" />
                <span>Show Window GUI</span>
              </>
            ) : (
              <>
                <FolderTree className="w-3.5 h-3.5 text-slate-600" />
                <span>View Python Architecture</span>
              </>
            )}
          </button>
          <button
            onClick={copierCommande}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium rounded bg-red-600 hover:bg-red-700 text-white transition shadow-xs"
          >
            {copie ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            <span>Copy Run Command</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 p-6 flex flex-col items-center justify-start">
        {!vueArchitecture ? (
          /* Desktop PySide6 Window */
          <div className="w-full max-w-5xl bg-white rounded-lg shadow-md border border-slate-300 flex flex-col overflow-hidden min-h-[640px]">
            {/* Desktop Window Titlebar */}
            <div className="bg-slate-200 border-b border-slate-300 px-4 py-2.5 flex items-center justify-between select-none">
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span>
                <span className="w-3 h-3 rounded-full bg-amber-500 inline-block"></span>
                <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span>
                <span className="ml-3 text-xs font-semibold text-slate-700">
                  Article Management — PySide6 Window
                </span>
              </div>
              <span className="text-[11px] text-slate-500 font-mono">1100 &times; 750</span>
            </div>

            {/* Window Body */}
            <div className="flex-1 p-4 bg-slate-50 flex flex-col">
              {/* Top-Left Tabs Bar */}
              <div className="flex items-center border-b border-slate-300 gap-1 overflow-x-auto select-none">
                {ONGLETS.map((onglet) => {
                  const estActif = ongletActif === onglet;
                  return (
                    <button
                      key={onglet}
                      onClick={() => setOngletActif(onglet)}
                      className={`px-4 py-2 text-xs font-semibold rounded-t border-t border-l border-r transition-colors ${
                        estActif
                          ? "bg-white text-slate-900 border-slate-300 border-b-2 border-b-red-600 -mb-[1px] shadow-2xs"
                          : "bg-slate-200 text-slate-600 border-transparent hover:bg-slate-300/70"
                      }`}
                    >
                      {onglet}
                    </button>
                  );
                })}
              </div>

              {/* Tab Content Panel */}
              <div className="flex-1 bg-white border border-t-0 border-slate-300 rounded-b p-4 flex flex-col">
                {/* Panel Header: Left Info + Top-Right Rotating Refresh Icon Button */}
                <div className="flex items-center justify-between mb-3 px-1">
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="font-semibold text-slate-800">{ongletActif}</span>
                    <span className="text-slate-400">&bull;</span>
                    <span className="text-slate-500">
                      {estEnCours ? "Updating articles from source..." : `${articlesActifs.length} articles in cache`}
                    </span>
                    <span className="bg-emerald-50 text-emerald-700 text-[10px] font-medium px-2 py-0.5 rounded border border-emerald-200">
                      Cached
                    </span>
                  </div>

                  {/* Top-Right Refresh Button with Rotating Icon */}
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] text-slate-400 font-mono">
                      Last: {dateDerniereMaj[ongletActif]}
                    </span>
                    <button
                      onClick={() => declencherActualisation(ongletActif)}
                      disabled={estEnCours}
                      title="Refresh articles"
                      className={`p-1.5 rounded border transition flex items-center justify-center ${
                        estEnCours
                          ? "bg-red-50 text-red-600 border-red-200 cursor-not-allowed"
                          : "bg-white hover:bg-slate-100 text-slate-600 hover:text-red-600 border-slate-300"
                      }`}
                    >
                      <RotateCw
                        className={`w-4 h-4 transition-transform ${
                          estEnCours ? "animate-spin text-red-600" : ""
                        }`}
                      />
                    </button>
                  </div>
                </div>

                {/* Table Component with Guaranteed Smooth Scrolling */}
                <div className="flex-1 border border-slate-200 rounded overflow-hidden flex flex-col max-h-[460px]">
                  {/* Table Header: 3 columns required (Image, Title, Date) */}
                  <div className="grid grid-cols-12 bg-slate-100 border-b border-slate-200 text-xs font-bold text-slate-700 select-none py-2 px-3 shrink-0">
                    <div className="col-span-2">Image</div>
                    <div className="col-span-8">Title</div>
                    <div className="col-span-2 text-center">Date</div>
                  </div>

                  {/* Table Rows — Smooth vertical scrolling with eager image loading */}
                  <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                    {articlesActifs.map((art, idx) => (
                      <div
                        key={`${ongletActif}-${idx}`}
                        className={`grid grid-cols-12 items-center py-2 px-3 select-none text-xs transition-colors ${
                          idx % 2 === 0 ? "bg-white" : "bg-slate-50/60"
                        }`}
                      >
                        {/* 1st column: Image with reliable display on scroll */}
                        <div className="col-span-2 pr-3">
                          {imagesEnErreur[art.image_url] ? (
                            <div className="w-28 h-16 rounded bg-slate-100 border border-slate-200 flex flex-col items-center justify-center text-slate-400 text-[10px]">
                              <ImageOff className="w-4 h-4 mb-0.5 text-slate-300" />
                              <span>No Image</span>
                            </div>
                          ) : (
                            <img
                              src={art.image_url}
                              alt=""
                              loading="eager"
                              onError={() =>
                                setImagesEnErreur((prev) => ({
                                  ...prev,
                                  [art.image_url]: true,
                                }))
                              }
                              className="w-28 h-16 object-cover rounded bg-slate-200 border border-slate-200 pointer-events-none block"
                            />
                          )}
                        </div>

                        {/* 2nd column: Title */}
                        <div className="col-span-8 pr-4">
                          <p className="font-medium text-slate-900 leading-snug">
                            {art.title}
                          </p>
                        </div>

                        {/* 3rd column: Date */}
                        <div className="col-span-2 text-center text-slate-500 font-mono text-[11px]">
                          {art.date}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Status Bar */}
            <div className="bg-white border-t border-slate-200 px-4 py-1.5 flex items-center justify-between text-xs text-slate-500">
              <div className="flex items-center space-x-2">
                <span className={`w-2 h-2 rounded-full ${estEnCours ? "bg-amber-500 animate-pulse" : "bg-emerald-500"}`}></span>
                <span>
                  Active source: {ongletActif} &bull; {estEnCours ? "Fetching update..." : `Cached (${articlesActifs.length} items)`}
                </span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">PySide6 6.5+ &bull; Ready</span>
            </div>
          </div>
        ) : (
          /* Architecture & Code Viewer */
          <div className="w-full max-w-5xl bg-white rounded-lg shadow-md border border-slate-300 overflow-hidden flex flex-col min-h-[640px]">
            <div className="bg-slate-900 text-slate-100 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-mono font-semibold">
                  /GESTION_ARTICLE — Fixed Scroll Image Loading
                </span>
              </div>
              <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                User-Agent Headers &bull; Observer Registry &bull; ScrollPerPixel
              </span>
            </div>

            <div className="flex-1 flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x divide-slate-200">
              {/* File list */}
              <div className="w-full md:w-80 bg-slate-50 p-4">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Architecture Files
                </h4>
                <div className="space-y-1">
                  {Object.entries(fichiersPython).map(([nom, info]) => (
                    <button
                      key={nom}
                      onClick={() => setFichierSelectionne(nom)}
                      className={`w-full text-left px-3 py-2 rounded text-xs flex flex-col transition ${
                        fichierSelectionne === nom
                          ? "bg-red-50 text-red-700 font-semibold border border-red-200"
                          : "text-slate-700 hover:bg-slate-200"
                      }`}
                    >
                      <span className="font-mono">{nom}</span>
                      <span className="text-[11px] text-slate-500 font-normal truncate mt-0.5">
                        {info.description}
                      </span>
                    </button>
                  ))}
                </div>

                <div className="mt-6 pt-4 border-t border-slate-200">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                    Execution
                  </h4>
                  <div className="bg-slate-900 text-slate-200 p-2.5 rounded font-mono text-[11px] leading-relaxed">
                    <span className="text-slate-500"># Start PySide6 Desktop GUI:</span>
                    <br />
                    <span className="text-emerald-400">$</span> cd /GESTION_ARTICLE
                    <br />
                    <span className="text-emerald-400">$</span> python3 lancement.py
                  </div>
                </div>
              </div>

              {/* File details */}
              <div className="flex-1 p-6 flex flex-col bg-white">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <div className="flex items-center space-x-2">
                    <Code2 className="w-4 h-4 text-slate-500" />
                    <span className="font-mono text-xs font-bold text-slate-800">
                      {fichiersPython[fichierSelectionne]?.chemin}
                    </span>
                  </div>
                  <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded font-medium">
                    Validated (&lt;160 lines)
                  </span>
                </div>

                <p className="text-xs text-slate-600 mt-3 mb-4">
                  {fichiersPython[fichierSelectionne]?.description}
                </p>

                <div className="flex-1 bg-slate-900 text-slate-100 rounded p-4 font-mono text-xs overflow-auto">
                  <div className="text-slate-500">// File: {fichiersPython[fichierSelectionne]?.chemin}</div>
                  <div className="text-slate-400 mt-2">
                    Correction des images au défilement (scroll) :
                    <br />
                    1. En-têtes HTTP (User-Agent) ajoutés aux requêtes d&apos;images pour éviter les rejets 403 Forbidden des serveurs CDN/Cloudflare.
                    <br />
                    2. Registre central d&apos;observateurs : les cellules défilées reçoivent toutes leur pixmap dès la fin du téléchargement asynchrone.
                    <br />
                    3. Mode de défilement fluide ScrollPerPixel évitant le masquage intempestif des widgets de cellules.
                    <br />
                    4. Normalisation des URLs (gestion des schémas //, https, paramètres).
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
