import React, { useState, useEffect, useCallback } from 'react';
import RoomScene from './components/RoomScene';
import Controls from './components/Controls';
import { RoomState } from './types';
import { processCommand } from './services/geminiService';
import * as api from './services/apiService';

const INITIAL_STATE: RoomState = {
  brightness: 40,
  lightColor: '#ffffff',
  blindsPosition: 0,
  temperature: 19,
  targetTemperature: 21,
  isTvOn: false,
  isHeaterOn: false
};

const App: React.FC = () => {
  const [roomState, setRoomState] = useState<RoomState>(INITIAL_STATE);
  const [isProcessing, setIsProcessing] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Fetch initial state and poll for updates
  useEffect(() => {
    const fetchStatus = async () => {
      const status = await api.getStatus();
      if (status && status.success) {
        setIsConnected(true);
        // Map backend state to room state
        const luces = status.devices.filter(d => d.type === 'luz');
        const enchufes = status.devices.filter(d => d.type === 'enchufe');
        
        if (luces.length > 0) {
          const luz = luces[0]; // Use first light as reference (luz_salon)
          const isLightOn = luz.estado === 'ON';
          setRoomState(prev => ({
            ...prev,
            // If light is OFF, brightness should be 0 for display, otherwise use stored brightness
            brightness: isLightOn ? luz.brightness : 0,
            lightColor: luz.color,
            blindsPosition: luz.curtains,
            temperature: luz.temperature,
            targetTemperature: luz.target_temperature,
            isTvOn: enchufes.find(e => e.id.includes('tv'))?.estado === 'ON',
            isHeaterOn: enchufes.find(e => e.id.includes('calefactor'))?.estado === 'ON',
          }));
        }
      } else {
        setIsConnected(false);
      }
    };

    // Initial fetch
    fetchStatus();

    // Poll every 2 seconds
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  // Temperature simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setRoomState(prev => {
        if (Math.abs(prev.temperature - prev.targetTemperature) < 0.1) return prev;
        
        const change = prev.targetTemperature > prev.temperature ? 0.1 : -0.1;
        return {
          ...prev,
          temperature: Number((prev.temperature + change).toFixed(1))
        };
      });
    }, 2000); 

    return () => clearInterval(interval);
  }, []);

  const handleUpdateState = useCallback(async (newState: Partial<RoomState>) => {
    setRoomState(prev => ({ ...prev, ...newState }));
    
    // Send updates to backend
    try {
      if ('brightness' in newState && newState.brightness !== undefined) {
        await api.setBrightness('luz_salon', newState.brightness);
        // If brightness > 0, turn light ON; if brightness = 0, turn light OFF
        if (newState.brightness > 0) {
          await api.controlDevice('luz_salon', 'ON');
        } else {
          await api.controlDevice('luz_salon', 'OFF');
        }
      }
      if ('lightColor' in newState) {
        await api.setColor('luz_salon', newState.lightColor!);
      }
      if ('blindsPosition' in newState) {
        await api.setCurtains(newState.blindsPosition!);
      }
      if ('targetTemperature' in newState) {
        await api.setTemperature(newState.targetTemperature!);
      }
      if ('isTvOn' in newState) {
        await api.controlDevice('enchufe_tv', newState.isTvOn ? 'ON' : 'OFF');
      }
      if ('isHeaterOn' in newState) {
        await api.controlDevice('enchufe_calefactor', newState.isHeaterOn ? 'ON' : 'OFF');
      }
    } catch (error) {
      console.error('Error updating backend:', error);
    }
  }, []);

  const handleCommand = async (text: string) => {
    setIsProcessing(true);
    setNotification("Procesando...");
    
    try {
      const result = await processCommand(text, roomState);
      
      if (result.newState && Object.keys(result.newState).length > 0) {
        handleUpdateState(result.newState);
      }
      
      setNotification(result.text);
      setTimeout(() => setNotification(null), 4000);
    } catch (error) {
        console.error(error);
        setNotification("Error.");
        setTimeout(() => setNotification(null), 3000);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="relative w-full h-screen bg-slate-900 overflow-hidden">
      <RoomScene roomState={roomState} />

      <Controls 
        state={roomState} 
        onUpdate={handleUpdateState} 
        onCommand={handleCommand}
        isProcessing={isProcessing}
      />

      {/* Connection Status Indicator */}
      <div className="absolute top-4 left-4 z-50">
        <div className={`flex items-center gap-2 px-3 py-2 rounded-full text-xs font-medium backdrop-blur-md ${
          isConnected 
            ? 'bg-emerald-900/80 text-emerald-100 border border-emerald-500/30' 
            : 'bg-red-900/80 text-red-100 border border-red-500/30'
        }`}>
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse`}></div>
          <span>{isConnected ? 'Conectado al servidor' : 'Desconectado'}</span>
        </div>
      </div>

      {notification && (
        <div className="absolute top-8 left-1/2 -translate-x-1/2 pointer-events-none z-50">
          <div className="bg-slate-900/90 backdrop-blur border border-emerald-500/30 text-emerald-100 px-6 py-3 rounded-full shadow-lg flex items-center gap-3 animate-fade-in-down">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium">{notification}</span>
          </div>
        </div>
      )}
      
      {!process.env.API_KEY && (
         <div className="absolute bottom-4 left-4 text-red-500 bg-black/80 p-2 rounded text-xs z-50">
            Warning: process.env.API_KEY is missing.
         </div>
      )}
    </div>
  );
};

export default App;