import React from "react";

export function PromoCard() {
    return (
        <div className="bg-gradient-to-br from-primary to-primary-dark rounded-xl shadow-lg border border-primary/20 p-6 text-white relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-2xl group-hover:scale-125 transition-transform duration-700"></div>
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-black/10 rounded-full -ml-12 -mb-12 blur-xl"></div>

            <div className="relative z-10">
                <div className="bg-white/20 w-10 h-10 rounded-lg flex items-center justify-center mb-4 backdrop-blur-sm border border-white/20">
                    <span className="material-symbols-outlined text-[24px]">rocket_launch</span>
                </div>
                <h4 className="text-lg font-bold mb-2">Coming Soon</h4>
                <p className="text-xs text-white/80 leading-relaxed mb-6 font-medium">
                    Mock Interviews with AI Avatars. Get ready for life-like video practice sessions.
                </p>
                <div className="inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest bg-white/20 px-3 py-1 rounded-full border border-white/30 backdrop-blur-sm">
                    Exclusive Beta
                </div>
            </div>
        </div>
    );
}
