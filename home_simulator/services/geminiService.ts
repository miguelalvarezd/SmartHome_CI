import { GoogleGenAI, FunctionDeclaration, Type } from "@google/genai";
import { RoomState } from "../types";

const controlHomeFunction: FunctionDeclaration = {
  name: 'controlHome',
  description: 'Controlar los dispositivos de la casa inteligente (luces, persianas, temperatura, TV, calefactor).',
  parameters: {
    type: Type.OBJECT,
    properties: {
      brightness: {
        type: Type.NUMBER,
        description: 'Brillo de la luz de 0 a 100.',
      },
      lightColor: {
        type: Type.STRING,
        description: 'Color de la luz en formato hexadecimal (ej: #ff0000 para rojo).',
      },
      blindsPosition: {
        type: Type.NUMBER,
        description: 'Posición de las persianas de 0 (cerradas) a 100 (abiertas).',
      },
      targetTemperature: {
        type: Type.NUMBER,
        description: 'Temperatura objetivo en grados Celsius.',
      },
      isTvOn: {
        type: Type.BOOLEAN,
        description: 'Encender (true) o apagar (false) la televisión.',
      },
      isHeaterOn: {
        type: Type.BOOLEAN,
        description: 'Encender (true) o apagar (false) el calefactor.',
      }
    },
  },
};

export const processCommand = async (
  command: string,
  currentState: RoomState
): Promise<{ text: string; newState?: Partial<RoomState> }> => {
  try {
    const apiKey = process.env.API_KEY;
    if (!apiKey) {
      return { text: "Error: API Key no encontrada." };
    }

    const ai = new GoogleGenAI({ apiKey });
    
    // Context about current state
    const context = `
      El estado actual de la habitación es:
      - Brillo: ${currentState.brightness}%
      - Color Luz: ${currentState.lightColor}
      - Persianas: ${currentState.blindsPosition}% abiertas
      - Temperatura: ${currentState.temperature}°C (Target: ${currentState.targetTemperature}°C)
      - TV: ${currentState.isTvOn ? 'Encendida' : 'Apagada'}
      - Calefactor: ${currentState.isHeaterOn ? 'Encendido' : 'Apagado'}
      
      Eres Jarvis, un asistente de domótica. Responde de forma muy breve y natural.
    `;

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: `${context}\nUser command: ${command}`,
      config: {
        tools: [{ functionDeclarations: [controlHomeFunction] }],
        systemInstruction: "Controla la casa según el usuario. Si pide 'modo cine', apaga luces (o ponlas muy bajas y azules), baja persianas, enciende TV y ajusta temperatura a 22. Si dice 'hace frío', sube temperatura y enciende calefactor.",
      },
    });

    const candidate = response.candidates?.[0];
    const modelText = candidate?.content?.parts?.find(p => p.text)?.text || "Hecho.";
    
    let newState: Partial<RoomState> = {};
    
    // Check for function calls
    const functionCalls = candidate?.content?.parts?.filter(p => p.functionCall).map(p => p.functionCall);

    if (functionCalls && functionCalls.length > 0) {
      const call = functionCalls[0];
      if (call && call.args) {
         const args = call.args as Record<string, any>;
         if (typeof args.brightness === 'number') newState.brightness = args.brightness;
         if (typeof args.lightColor === 'string') newState.lightColor = args.lightColor;
         if (typeof args.blindsPosition === 'number') newState.blindsPosition = args.blindsPosition;
         if (typeof args.targetTemperature === 'number') newState.targetTemperature = args.targetTemperature;
         if (typeof args.isTvOn === 'boolean') newState.isTvOn = args.isTvOn;
         if (typeof args.isHeaterOn === 'boolean') newState.isHeaterOn = args.isHeaterOn;
      }
    }

    return { text: modelText, newState };

  } catch (error) {
    console.error("Gemini API Error:", error);
    return { text: "Lo siento, hubo un error al procesar tu solicitud." };
  }
};