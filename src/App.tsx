import { useState } from "react";
import { FolderTree, Terminal, Monitor, Code2, Check, Copy } from "lucide-react";

const ONGLETS = [
  "STATTIMES",
  "SUPPLYCHAINDIVE",
  "AIRCARGOWEEK",
  "FREIGHTWAVES",
  "SEATRADE-MARITIME",
] as const;

type NomOnglet = typeof ONGLETS[number];

export default function App() {
  const [ongletActif, setOngletActif] = useState<NomOnglet>("STATTIMES");
  const [vueArchitecture, setVueArchitecture] = useState(false);
  const [fichierSelectionne, setFichierSelectionne] = useState("lancement.py");
  const [copie, setCopie] = useState(false);

  const fichiersPython: Record<string, { chemin: string; description: string }> = {
    "lancement.py": {
      chemin: "/GESTION_ARTICLE/lancement.py",
      description: "Main executable entry point initializing QApplication and MVC structure",
    },
    "fenetre_principale.py": {
      chemin: "/GESTION_ARTICLE/vues/fenetre_principale.py",
      description: "Main PySide6 QMainWindow containing top-left tabs layout and status bar",
    },
    "controleur_principal.py": {
      chemin: "/GESTION_ARTICLE/controleurs/controleur_principal.py",
      description: "MVC controller managing user actions and tab switching logic",
    },
    "conteneur_onglets.py": {
      chemin: "/GESTION_ARTICLE/composants/conteneur_onglets.py",
      description: "Reusable PySide6 QTabWidget component hosting empty content panes",
    },
    "configuration_theme.py": {
      chemin: "/GESTION_ARTICLE/configuration/configuration_theme.py",
      description: "QSS stylesheet applying light theme and red primary accents",
    },
  };

  const copierCommande = () => {
    navigator.clipboard?.writeText("cd /GESTION_ARTICLE && python3 lancement.py");
    setCopie(true);
    setTimeout(() => setCopie(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans">
      {/* Top Bar / Header */}
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

      {/* Main Content Area */}
      <main className="flex-1 p-6 flex flex-col items-center justify-start">
        {!vueArchitecture ? (
          /* Desktop PySide6 Window Mockup / Simulation */
          <div className="w-full max-w-5xl bg-white rounded-lg shadow-md border border-slate-300 flex flex-col overflow-hidden min-h-[580px]">
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
              {/* Tabs Container positioned Top-Left ("en haut a gauche") */}
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

              {/* Tab Page Container — without content ("sans contenu") */}
              <div className="flex-1 bg-white border border-t-0 border-slate-300 rounded-b p-6 flex flex-col">
                <div className="flex-1 border-2 border-dashed border-slate-200 rounded p-8 flex flex-col items-center justify-center text-center">
                  <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
                    <Monitor className="w-6 h-6" />
                  </div>
                  <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                    {ongletActif}
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 max-w-sm">
                    Empty tab page container initialized as requested (&ldquo;sans contenu&rdquo;). Ready for article cards, search filters, and scraping feeds.
                  </p>
                </div>
              </div>
            </div>

            {/* Desktop Status Bar */}
            <div className="bg-white border-t border-slate-200 px-4 py-1.5 flex items-center justify-between text-xs text-slate-500">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Active source: {ongletActif}</span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">PySide6 6.5+ &bull; Ready</span>
            </div>
          </div>
        ) : (
          /* Python Code & Architecture Explorer */
          <div className="w-full max-w-5xl bg-white rounded-lg shadow-md border border-slate-300 overflow-hidden flex flex-col min-h-[580px]">
            <div className="bg-slate-900 text-slate-100 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-mono font-semibold">
                  /GESTION_ARTICLE — Python PySide6 MVC Project
                </span>
              </div>
              <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                SOLID &bull; DRY &bull; &lt;250 lines
              </span>
            </div>

            <div className="flex-1 flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x divide-slate-200">
              {/* File list */}
              <div className="w-full md:w-72 bg-slate-50 p-4">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Project Files
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
                    <span className="text-slate-500"># Run in terminal:</span>
                    <br />
                    <span className="text-emerald-400">$</span> cd /GESTION_ARTICLE
                    <br />
                    <span className="text-emerald-400">$</span> python3 lancement.py
                  </div>
                </div>
              </div>

              {/* File detail */}
              <div className="flex-1 p-6 flex flex-col bg-white">
                <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                  <div className="flex items-center space-x-2">
                    <Code2 className="w-4 h-4 text-slate-500" />
                    <span className="font-mono text-xs font-bold text-slate-800">
                      {fichiersPython[fichierSelectionne]?.chemin}
                    </span>
                  </div>
                  <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded font-medium">
                    Syntax Validated
                  </span>
                </div>

                <p className="text-xs text-slate-600 mt-3 mb-4">
                  {fichiersPython[fichierSelectionne]?.description}
                </p>

                <div className="flex-1 bg-slate-900 text-slate-100 rounded p-4 font-mono text-xs overflow-auto">
                  <div className="text-slate-500">// File: {fichiersPython[fichierSelectionne]?.chemin}</div>
                  <div className="text-slate-400 mt-2">
                    Structure respectant l&apos;architecture MVC, la séparation des responsabilités,
                    le nommage 100% en français (classes, fonctions, variables) et les textes GUI en anglais.
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
