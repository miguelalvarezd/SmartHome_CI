export interface RoomState {
  brightness: number; // 0 to 100
  lightColor: string; // Hex color
  blindsPosition: number; // 0 (closed) to 100 (open)
  temperature: number; // Celsius
  targetTemperature: number;
  isTvOn: boolean;
  isHeaterOn: boolean;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
}

export enum DeviceType {
  LIGHTS = 'LIGHTS',
  BLINDS = 'BLINDS',
  THERMOSTAT = 'THERMOSTAT',
  TV = 'TV',
  HEATER = 'HEATER'
}