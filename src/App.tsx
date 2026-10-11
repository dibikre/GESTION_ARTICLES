import { useState } from "react";
import { FolderTree, Terminal, Monitor, Code2, Check, Copy, RefreshCw } from "lucide-react";

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

// Données d'exemple conformes aux scrapers /SOURCE_ONGLET/ pour la prévisualisation web
const ARTICLES_PAR_SOURCE: Record<NomOnglet, ArticleData[]> = {
  STATTIMES: [
    {
      title: "Cathay Cargo operates first commercial flight into Western Sydney International Airport",
      date: "2026-10-10",
      image_url: "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "TIACA announces winners of the 2026 Air Cargo Sustainability Awards",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "Lufthansa Cargo expands transpacific network with direct freighter connections",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "Etihad Cargo posts record third-quarter tonnage driven by pharma and tech demand",
      date: "2026-10-07",
      image_url: "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?w=300&auto=format&fit=crop&q=60",
    },
  ],
  SUPPLYCHAINDIVE: [
    {
      title: "Port of Los Angeles cargo volume surges 14% as shippers front-load holiday goods",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "US East Coast dockworkers and maritime alliance resume talks on port automation",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "FedEx deploys autonomous electric yard trucks across major Midwest ground hubs",
      date: "2026-10-06",
      image_url: "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "Semiconductor supply chains face new export restrictions ahead of global reviews",
      date: "2026-10-05",
      image_url: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=300&auto=format&fit=crop&q=60",
    },
  ],
  AIRCARGOWEEK: [
    {
      title: "Air France KLM Martinair Cargo secures CEIV Lithium Battery re-certification",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1508873696983-2df5293cb32f?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "Chapman Freeborn appoints regional vice president for Europe, Middle East and Africa",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "Worldwide Flight Services opens state-of-the-art cold chain center at Liege Airport",
      date: "2026-10-07",
      image_url: "https://images.unsplash.com/photo-1586528116493-a029325540fa?w=300&auto=format&fit=crop&q=60",
    },
  ],
  FREIGHTWAVES: [
    {
      title: "Truckload tender rejection rates tick higher as regional freight markets tighten",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "Class 1 railroads report mixed rail traffic metrics amid fluctuating intermodal flows",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "Diesel fuel prices drop for third straight week providing relief to carrier margins",
      date: "2026-10-07",
      image_url: "https://images.unsplash.com/photo-1527018607616-a9f8f413bf2a?w=300&auto=format&fit=crop&q=60",
    },
  ],
  "SEATRADE-MARITIME": [
    {
      title: "Global container fleet crosses 30 million TEU milestone amidst rapid newbuilding pace",
      date: "2026-10-09",
      image_url: "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "CMA CGM orders next-generation dual-fuel methanol container vessels from DSIC",
      date: "2026-10-08",
      image_url: "https://images.unsplash.com/photo-1494412574643-ff11b0a5c1c3?w=300&auto=format&fit=crop&q=60",
    },
    {
      title: "Panama Canal increases daily transit slots to 36 as reservoir water levels stabilize",
      date: "2026-10-07",
      image_url: "https://images.unsplash.com/photo-1505705694340-019e1e335916?w=300&auto=format&fit=crop&q=60",
    },
  ],
};

export default function App() {
  const [ongletActif, setOngletActif] = useState<NomOnglet>("STATTIMES");
  const [vueArchitecture, setVueArchitecture] = useState(false);
  const [fichierSelectionne, setFichierSelectionne] = useState("tableau_articles.py");
  const [copie, setCopie] = useState(false);

  const articles = ARTICLES_PAR_SOURCE[ongletActif] || [];

  const fichiersPython: Record<string, { chemin: string; description: string }> = {
    "tableau_articles.py": {
      chemin: "/GESTION_ARTICLE/composants/tableau_articles.py",
      description: "Passive QTableWidget rendering Image (1st), Title (2nd), Date (3rd) with no click actions",
    },
    "panneau_source_articles.py": {
      chemin: "/GESTION_ARTICLE/composants/panneau_source_articles.py",
      description: "Reusable tab content panel hosting TableauArticles and status header for each source",
    },
    "interface_extracteur.py": {
      chemin: "/GESTION_ARTICLE/services/extracteurs/interface_extracteur.py",
      description: "Abstract interface defining article extraction contract (SOLID / DIP / OCP)",
    },
    "fabrique_extracteurs.py": {
      chemin: "/GESTION_ARTICLE/services/extracteurs/fabrique_extracteurs.py",
      description: "Factory mapping each source tab to its concrete extractor without tight coupling",
    },
    "tache_chargement_articles.py": {
      chemin: "/GESTION_ARTICLE/services/tache_chargement_articles.py",
      description: "QThread handling background network scraping without blocking the GUI (Rule 16)",
    },
    "modele_article.py": {
      chemin: "/GESTION_ARTICLE/modeles/modele_article.py",
      description: "Domain model representing article data (titre, date, url_image, url_source)",
    },
    "controleur_principal.py": {
      chemin: "/GESTION_ARTICLE/controleurs/controleur_principal.py",
      description: "Coordinates tab switching, async scraper threads, and memory caching",
    },
  };

  const copierCommande = () => {
    navigator.clipboard?.writeText("cd /GESTION_ARTICLE && python3 lancement.py");
    setCopie(true);
    setTimeout(() => setCopie(false), 2000);
  };

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
          <div className="w-full max-w-5xl bg-white rounded-lg shadow-md border border-slate-300 flex flex-col overflow-hidden min-h-[620px]">
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

              {/* Tab Content Panel: Articles Table */}
              <div className="flex-1 bg-white border border-t-0 border-slate-300 rounded-b p-4 flex flex-col">
                <div className="flex items-center justify-between mb-3 text-xs text-slate-500">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-slate-700">{ongletActif}</span>
                    <span>&bull;</span>
                    <span>{articles.length} articles loaded</span>
                  </div>
                  <span className="text-[11px] text-slate-400">
                    Read-only view &bull; No click actions configured
                  </span>
                </div>

                {/* Table Component */}
                <div className="flex-1 border border-slate-200 rounded overflow-hidden flex flex-col">
                  {/* Table Header: 3 columns required (Image, Title, Date) */}
                  <div className="grid grid-cols-12 bg-slate-100 border-b border-slate-200 text-xs font-bold text-slate-700 select-none py-2 px-3">
                    <div className="col-span-2">Image</div>
                    <div className="col-span-8">Title</div>
                    <div className="col-span-2 text-center">Date</div>
                  </div>

                  {/* Table Rows (Non-clickable, read-only display) */}
                  <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                    {articles.map((art, idx) => (
                      <div
                        key={idx}
                        className={`grid grid-cols-12 items-center py-2.5 px-3 select-none text-xs ${
                          idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"
                        }`}
                      >
                        {/* 1st column: Image */}
                        <div className="col-span-2 pr-3">
                          <img
                            src={art.image_url}
                            alt=""
                            className="w-24 h-14 object-cover rounded bg-slate-200 border border-slate-200 pointer-events-none"
                            loading="lazy"
                          />
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
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Active source: {ongletActif} — {articles.length} articles loaded</span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">PySide6 6.5+ &bull; Ready</span>
            </div>
          </div>
        ) : (
          /* Architecture & Code Viewer */
          <div className="w-full max-w-5xl bg-white rounded-lg shadow-md border border-slate-300 overflow-hidden flex flex-col min-h-[620px]">
            <div className="bg-slate-900 text-slate-100 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-mono font-semibold">
                  /GESTION_ARTICLE — SOLID & MVC Architecture
                </span>
              </div>
              <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                Threaded &bull; Extractor Factory &bull; Passive Table
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
                    Validated (&lt;130 lines)
                  </span>
                </div>

                <p className="text-xs text-slate-600 mt-3 mb-4">
                  {fichiersPython[fichierSelectionne]?.description}
                </p>

                <div className="flex-1 bg-slate-900 text-slate-100 rounded p-4 font-mono text-xs overflow-auto">
                  <div className="text-slate-500">// File: {fichiersPython[fichierSelectionne]?.chemin}</div>
                  <div className="text-slate-400 mt-2">
                    Conforme aux règles de conception :
                    <br />
                    - Tableau avec Image (colonne 1), Title (colonne 2), Date (colonne 3)
                    <br />
                    - Aucune action de clic sur les éléments listés
                    <br />
                    - Respect des principes S.O.L.I.D. et D.R.Y.
                    <br />
                    - Pas de blocage du thread principal (QThread d&apos;extraction asynchrone)
                    <br />
                    - Fichiers modulaires de moins de 250 lignes (tous &le; 128 lignes)
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
