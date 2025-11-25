import React, { useState } from 'react';
import { RoomState } from '../types';
import { Sun, Blinds, Thermometer, Palette, Settings2, X, Tv, Flame } from 'lucide-react';

interface ControlsProps {
  state: RoomState;
  onUpdate: (newState: Partial<RoomState>) => void;
  onCommand: (text: string) => Promise<void>;
  isProcessing: boolean;
}

const Controls: React.FC<ControlsProps> = ({ state, onUpdate, onCommand, isProcessing }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const colors = ['#ffffff', '#fef08a', '#fca5a5', '#86efac', '#93c5fd', '#c084fc', '#e11d48'];

  if (isCollapsed) {
    return (
      <div className="absolute top-4 right-4 z-10 pointer-events-auto animate-fade-in">
        <button
          onClick={() => setIsCollapsed(false)}
          className="bg-slate-900/80 backdrop-blur-md text-emerald-400 p-3 rounded-full shadow-lg border border-slate-700 hover:bg-slate-800 hover:text-emerald-300 transition-all transform hover:scale-105 group"
        >
          <Settings2 size={24} className="group-hover:rotate-90 transition-transform duration-500" />
        </button>
      </div>
    );
  }

  return (
    <div className="absolute inset-0 pointer-events-none flex flex-col justify-end md:justify-start md:items-end p-4 md:p-6 z-10">
      
      <div className="pointer-events-auto w-full md:w-80 bg-slate-900/90 backdrop-blur-xl border border-slate-700/50 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[55vh] md:max-h-[85vh] transition-all duration-300 animate-slide-in-right">
        
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-700/50 bg-slate-800/30 flex items-center justify-between shrink-0">
          <h2 className="text-white font-semibold text-sm flex items-center gap-2 tracking-wide">
            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] animate-pulse" />
            Smart Control
          </h2>
          <button 
            onClick={() => setIsCollapsed(true)}
            className="text-slate-400 hover:text-white p-1 hover:bg-slate-700/50 rounded-full transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-6 custom-scrollbar min-h-0">
          
          <div className="space-y-6 animate-fade-in">
            {/* Lighting */}
            <div className="space-y-3">
                <div className="flex items-center justify-between text-slate-200">
                  <div className="flex items-center gap-2 text-sm">
                    <Sun size={16} className="text-yellow-400" />
                    <span className="font-medium">Luces</span>
                  </div>
                  <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-400 border border-slate-700">{state.brightness}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={state.brightness}
                  onChange={(e) => onUpdate({ brightness: Number(e.target.value) })}
                  className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                />
                
                <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
                   {colors.map(c => (
                     <button
                        key={c}
                        onClick={() => onUpdate({ lightColor: c })}
                        className={`w-5 h-5 rounded-full border-2 transition-all hover:scale-110 flex-shrink-0 ${state.lightColor === c ? 'border-white scale-110 shadow-lg' : 'border-transparent opacity-70 hover:opacity-100'}`}
                        style={{ backgroundColor: c }}
                     />
                   ))}
                   <div className="relative w-5 h-5 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center overflow-hidden cursor-pointer flex-shrink-0 hover:bg-slate-600 transition-colors">
                      <input 
                        type="color" 
                        value={state.lightColor}
                        onChange={(e) => onUpdate({ lightColor: e.target.value })}
                        className="opacity-0 absolute w-full h-full cursor-pointer"
                      />
                      <Palette size={10} className="text-slate-400" />
                   </div>
                </div>
              </div>

              <div className="h-px bg-slate-700/50" />

              {/* Blinds */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-slate-200">
                  <div className="flex items-center gap-2 text-sm">
                    <Blinds size={16} className="text-blue-400" />
                    <span className="font-medium">Persianas</span>
                  </div>
                  <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-400 border border-slate-700">
                    {state.blindsPosition}%
                  </span>
                </div>
                 <div className="flex items-center gap-2">
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={state.blindsPosition}
                        onChange={(e) => onUpdate({ blindsPosition: Number(e.target.value) })}
                        className="flex-1 h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                    />
                 </div>
              </div>

              <div className="h-px bg-slate-700/50" />

              {/* Temperature */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-slate-200">
                  <div className="flex items-center gap-2 text-sm">
                    <Thermometer size={16} className="text-rose-400" />
                    <span className="font-medium">Clima</span>
                  </div>
                  <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-400 border border-slate-700">{state.targetTemperature}°C</span>
                </div>
                
                <div className="flex justify-between items-center bg-slate-800/50 border border-slate-700/50 p-2 rounded-xl">
                    <button 
                        onClick={() => onUpdate({ targetTemperature: Math.max(16, state.targetTemperature - 1) })}
                        className="w-8 h-8 flex items-center justify-center bg-slate-700 rounded-lg hover:bg-slate-600 text-white transition-colors"
                    >-</button>
                    <div className="text-xl font-bold text-white tabular-nums tracking-tight">{state.targetTemperature}°</div>
                    <button 
                        onClick={() => onUpdate({ targetTemperature: Math.min(30, state.targetTemperature + 1) })}
                        className="w-8 h-8 flex items-center justify-center bg-slate-700 rounded-lg hover:bg-slate-600 text-white transition-colors"
                    >+</button>
                </div>
              </div>

              <div className="h-px bg-slate-700/50" />

              {/* Devices Grid */}
              <div className="grid grid-cols-2 gap-3">
                 <button 
                    onClick={() => onUpdate({ isTvOn: !state.isTvOn })}
                    className={`flex flex-col items-center justify-center gap-2 p-3 rounded-xl border transition-all ${state.isTvOn ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300' : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:bg-slate-700/50'}`}
                 >
                    <Tv size={20} className={state.isTvOn ? 'drop-shadow-glow' : ''} />
                    <span className="text-xs font-medium">TV</span>
                 </button>

                 <button 
                    onClick={() => onUpdate({ isHeaterOn: !state.isHeaterOn })}
                    className={`flex flex-col items-center justify-center gap-2 p-3 rounded-xl border transition-all ${state.isHeaterOn ? 'bg-orange-500/20 border-orange-500/50 text-orange-300' : 'bg-slate-800/50 border-slate-700/50 text-slate-400 hover:bg-slate-700/50'}`}
                 >
                    <Flame size={20} className={state.isHeaterOn ? 'drop-shadow-glow' : ''} />
                    <span className="text-xs font-medium">Calefactor</span>
                 </button>
              </div>

            </div>

        </div>
      </div>
    </div>
  );
};

export default Controls;