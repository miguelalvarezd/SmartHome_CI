/**
 * API Service for SmartHome Backend Integration
 * Connects the 3D simulator with the Python domotics server
 */

const API_BASE_URL = 'http://localhost:8080/api';

export interface DeviceState {
  id: string;
  type: string;
  estado: string;
  auto_off: number;
  ultimo_cambio: string;
  brightness: number;
  color: string;
  curtains: number;
  temperature: number;
  target_temperature: number;
}

export interface SystemStatus {
  success: boolean;
  timestamp: string;
  devices: DeviceState[];
  total: number;
}

/**
 * Fetch current status from the server
 */
export async function getStatus(): Promise<SystemStatus | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/status`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching status:', error);
    return null;
  }
}

/**
 * Control a device (ON/OFF)
 */
export async function controlDevice(deviceId: string, action: 'ON' | 'OFF'): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/control`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: deviceId,
        action: action,
      }),
    });
    const data = await response.json();
    return data.success;
  } catch (error) {
    console.error('Error controlling device:', error);
    return false;
  }
}

/**
 * Set brightness for a light
 */
export async function setBrightness(deviceId: string, brightness: number): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/brightness`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: deviceId,
        brightness: brightness,
      }),
    });
    const data = await response.json();
    return data.success;
  } catch (error) {
    console.error('Error setting brightness:', error);
    return false;
  }
}

/**
 * Set color for a light
 */
export async function setColor(deviceId: string, color: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/color`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: deviceId,
        color: color,
      }),
    });
    const data = await response.json();
    return data.success;
  } catch (error) {
    console.error('Error setting color:', error);
    return false;
  }
}

/**
 * Set curtains position
 */
export async function setCurtains(position: number): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/curtains`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        position: position,
      }),
    });
    const data = await response.json();
    return data.success;
  } catch (error) {
    console.error('Error setting curtains:', error);
    return false;
  }
}

/**
 * Set target temperature
 */
export async function setTemperature(temperature: number): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/temperature`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        temperature: temperature,
      }),
    });
    const data = await response.json();
    return data.success;
  } catch (error) {
    console.error('Error setting temperature:', error);
    return false;
  }
}
