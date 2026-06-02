import React from "react";
import { Smile, Zap, Settings as SettingsIcon, Layers, Binary, MessageSquare, Code, Save } from "lucide-react";

export function AIPreferencesTab() {
    return (
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden relative transition-colors">
            <div className="h-1.5 w-full bg-primary absolute top-0 left-0"></div>

            <div className="p-8 md:p-10 border-b border-gray-100 dark:border-gray-800">
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                    <div className="max-w-md">
                        <h3 className="text-lg font-black text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                            <Smile className="text-primary" />
                            Interview Persona
                        </h3>
                        <p className="text-sm text-slate-500 dark:text-gray-400 font-medium">
                            Choose the personality of your AI interviewer. This affects tone, pressure level, and follow-up question style.
                        </p>
                    </div>
                    <div className="flex bg-slate-100 dark:bg-gray-950 p-1.5 rounded-xl shrink-0 h-fit border border-gray-200 dark:border-gray-800 shadow-inner">
                        {['strict', 'balanced', 'supportive'].map(mode => (
                            <label key={mode} className="cursor-pointer relative">
                                <input type="radio" name="persona" value={mode} className="peer sr-only" defaultChecked={mode === 'balanced'} />
                                <span className="block px-4 py-2 rounded-lg text-sm font-bold text-slate-500 dark:text-gray-400 transition-all peer-checked:bg-white dark:peer-checked:bg-gray-800 peer-checked:text-slate-900 dark:peer-checked:text-white peer-checked:shadow-sm capitalize">
                                    {mode}
                                </span>
                            </label>
                        ))}
                    </div>
                </div>
                <div className="mt-8 p-5 rounded-xl bg-slate-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-800 flex items-start gap-4">
                    <div className="p-2 bg-primary/10 rounded-lg shrink-0">
                        <Zap className="text-primary" size={20} />
                    </div>
                    <p className="text-sm text-slate-700 dark:text-gray-300 font-medium leading-relaxed mt-0.5">
                        <strong className="text-slate-900 dark:text-white font-black">Balanced Mode:</strong> The AI will maintain a professional demeanor, challenging you appropriately while offering constructive guidance if you get stuck during problem solving. Ideal for general practice.
                    </p>
                </div>
            </div>

            <div className="p-8 md:p-10 border-b border-gray-100 dark:border-gray-800">
                <h3 className="text-lg font-black text-slate-900 dark:text-white mb-8 flex items-center gap-2">
                    <SettingsIcon className="text-primary" />
                    Interaction Dynamics
                </h3>
                <div className="space-y-8">
                    <div className="flex items-center justify-between group">
                        <div className="flex flex-col gap-1 pr-4">
                            <label className="text-base font-bold text-slate-900 dark:text-white">Real-Time Feedback</label>
                            <p className="text-sm text-slate-500 dark:text-gray-400 font-medium">Receive immediate hints and corrections during your answer.</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer shrink-0">
                            <input type="checkbox" className="sr-only peer" defaultChecked />
                            <div className="w-12 h-7 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all dark:border-gray-600 peer-checked:bg-primary shadow-inner"></div>
                        </label>
                    </div>
                    <div className="flex items-center justify-between group">
                        <div className="flex flex-col gap-1 pr-4">
                            <label className="text-base font-bold text-slate-900 dark:text-white">Adaptive Difficulty</label>
                            <p className="text-sm text-slate-500 dark:text-gray-400 font-medium">AI automatically adjusts question complexity based on your performance history.</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer shrink-0">
                            <input type="checkbox" className="sr-only peer" />
                            <div className="w-12 h-7 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all dark:border-gray-600 peer-checked:bg-primary shadow-inner"></div>
                        </label>
                    </div>
                    <div className="flex flex-col gap-5 pt-4">
                        <div className="flex justify-between items-end">
                            <div className="flex flex-col gap-1">
                                <label className="text-base font-bold text-slate-900 dark:text-white">Response Timeout</label>
                                <p className="text-sm text-slate-500 dark:text-gray-400 font-medium">Maximum time allowed before the AI prompts for an answer.</p>
                            </div>
                            <span className="text-sm font-black text-primary bg-primary/10 px-3 py-1.5 rounded-lg border border-primary/20">2 min</span>
                        </div>
                        <input type="range" min="1" max="10" defaultValue="2" className="w-full h-2 bg-slate-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary" />
                        <div className="flex justify-between text-xs font-bold text-slate-400 px-1">
                            <span>30s</span>
                            <span>5m</span>
                            <span>10m</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-8 md:p-10">
                <h3 className="text-lg font-black text-slate-900 dark:text-white mb-6 flex items-center gap-2">
                    <Layers className="text-primary" />
                    Default Focus Areas
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                        { id: 'algos', title: 'Algorithms & Data Structures', desc: 'Sorting, graphs, trees, and dynamic programming.', icon: Binary, checked: true },
                        { id: 'system', title: 'System Design', desc: 'Scalability, database design, and architecture.', icon: Layers, checked: true },
                        { id: 'behavioral', title: 'Behavioral', desc: 'Leadership principles, conflict resolution, and soft skills.', icon: MessageSquare, checked: false },
                        { id: 'coding', title: 'Live Coding', desc: 'Syntax accuracy and clean code practices.', icon: Code, checked: false },
                    ].map(topic => (
                        <label key={topic.id} className="relative flex items-start p-5 cursor-pointer rounded-xl border border-gray-200 dark:border-gray-800 hover:bg-slate-50 dark:hover:bg-gray-800/50 transition-colors group">
                            <div className="flex h-6 items-center">
                                <input type="checkbox" defaultChecked={topic.checked} className="h-5 w-5 rounded border-gray-300 text-primary focus:ring-primary dark:border-gray-600 dark:bg-gray-900 shadow-sm transition-all" />
                            </div>
                            <div className="ml-4 text-sm">
                                <span className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                    <topic.icon size={14} className="text-slate-400 group-hover:text-primary transition-colors" /> {topic.title}
                                </span>
                                <p className="text-slate-500 dark:text-gray-400 mt-1 font-medium">{topic.desc}</p>
                            </div>
                        </label>
                    ))}
                </div>
            </div>

            <div className="px-8 py-5 bg-slate-50 dark:bg-gray-950/50 border-t border-gray-100 dark:border-gray-800 flex justify-end gap-4">
                <button className="px-5 py-2.5 text-sm font-bold text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white transition-colors">
                    Reset
                </button>
                <button className="px-6 py-2.5 bg-primary hover:bg-primary-dark text-white text-sm font-bold rounded-lg shadow-md shadow-primary/20 transition-all flex items-center gap-2">
                    <Save size={18} />
                    Save Config
                </button>
            </div>
        </div>
    );
}
