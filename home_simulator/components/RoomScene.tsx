import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, PerspectiveCamera, SoftShadows } from '@react-three/drei';
import { RoomState } from '../types';

interface RoomSceneProps {
  roomState: RoomState;
}

const BACKGROUND_COLOR = "#0f172a"; // Dark Slate 900 for app background

const Wall = (props: any) => (
  <mesh receiveShadow {...props}>
    <boxGeometry args={[props.width, props.height, props.depth]} />
    <meshStandardMaterial color="#f8fafc" roughness={0.5} />
  </mesh>
);

const Floor = () => (
  <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
    <planeGeometry args={[10, 10]} />
    <meshStandardMaterial color="#e2e8f0" roughness={0.6} />
  </mesh>
);

// Window on Left Wall (x = -5)
const WindowFrame = () => (
  <group position={[-4.95, 1, 0]} rotation={[0, Math.PI/2, 0]}>
    {/* Frame */}
    <mesh receiveShadow castShadow>
      <boxGeometry args={[3.2, 2.2, 0.2]} />
      <meshStandardMaterial color="#ffffff" />
    </mesh>
    {/* Glass */}
    <mesh position={[0, 0, 0.05]}>
      <planeGeometry args={[3, 2]} />
      <meshPhysicalMaterial 
        transparent 
        opacity={0.3} 
        color="#ffffff"
        roughness={0} 
        metalness={0.9} 
        transmission={0.5} 
      />
    </mesh>
    {/* Bright White Background ("Outside Daylight") */}
    <mesh position={[0, 0, -0.05]}>
        <planeGeometry args={[3, 2]} />
        <meshBasicMaterial color="#ffffff" toneMapped={false} />
    </mesh>
  </group>
);

// Blinds on Left Wall
const Blinds = ({ position }: { position: number }) => {
  const height = 2 * (1 - position / 100);

  return (
    <group position={[-4.85, 2, 0]} rotation={[0, Math.PI/2, 0]}>
       <mesh position={[0, -height / 2, 0]} castShadow receiveShadow>
         <boxGeometry args={[3.1, Math.max(0.1, height), 0.05]} />
         <meshStandardMaterial color="#1e3a8a" roughness={0.6} /> {/* Dark Blue */}
       </mesh>
    </group>
  );
};

// Sofa facing Back Wall (where TV is)
const Furniture = () => {
    return (
        <group>
            {/* Sofa Group positioned at Z=3, rotated to face -Z */}
            <group position={[0, -1.5, 3]} rotation={[0, Math.PI, 0]}>
                {/* Seat */}
                <mesh castShadow receiveShadow>
                    <boxGeometry args={[3, 1, 1.5]} />
                    <meshStandardMaterial color="#475569" />
                </mesh>
                {/* Arm R (Left in local) */}
                <mesh position={[-1.75, 0.25, 0]} castShadow receiveShadow>
                    <boxGeometry args={[0.5, 1.5, 1.5]} />
                    <meshStandardMaterial color="#475569" />
                </mesh>
                {/* Arm L (Right in local) */}
                <mesh position={[1.75, 0.25, 0]} castShadow receiveShadow>
                    <boxGeometry args={[0.5, 1.5, 1.5]} />
                    <meshStandardMaterial color="#475569" />
                </mesh>
                {/* Backrest */}
                <mesh position={[0, 0.75, -0.9]} castShadow receiveShadow>
                    <boxGeometry args={[4, 2.5, 0.3]} />
                    <meshStandardMaterial color="#475569" />
                </mesh>
            </group>

            {/* Coffee Table in middle (Z=1) */}
            <group position={[0, -1.6, 1]}>
                <mesh position={[0, 0, 0]} castShadow receiveShadow>
                    <cylinderGeometry args={[1, 1, 0.8, 32]} />
                    <meshStandardMaterial color="#1e293b" />
                </mesh>
                <mesh position={[0, 0.4, 0]} castShadow receiveShadow>
                    <cylinderGeometry args={[1.2, 1.2, 0.1, 32]} />
                    <meshStandardMaterial color="#0f172a" />
                </mesh>
            </group>
        </group>
    )
}

// Thermostat on Right Wall
const Thermostat = ({ temp, target }: { temp: number, target: number }) => {
    const color = temp < target ? '#3b82f6' : temp > target ? '#ef4444' : '#22c55e';
    
    return (
        <group position={[4.9, 1, 0]} rotation={[0, -Math.PI / 2, 0]}>
            <mesh castShadow receiveShadow>
                <boxGeometry args={[0.6, 0.8, 0.1]} />
                <meshStandardMaterial color="#f8fafc" />
            </mesh>
            <mesh position={[0, 0.1, 0.06]}>
                <planeGeometry args={[0.5, 0.4]} />
                <meshBasicMaterial color="#0f172a" />
            </mesh>
            <Text 
                position={[0, 0.1, 0.07]} 
                fontSize={0.15} 
                color={color}
                anchorX="center"
                anchorY="middle"
            >
                {temp.toFixed(1)}°C
            </Text>
            <Text 
                position={[0, -0.2, 0.07]} 
                fontSize={0.08} 
                color="#64748b"
                anchorX="center"
                anchorY="middle"
            >
                Target: {target}°
            </Text>
        </group>
    )
}

// TV on Back Wall
const TV = ({ isOn }: { isOn: boolean }) => {
    return (
        <group position={[0, 0.5, -4.9]} rotation={[0, 0, 0]}>
            {/* TV Frame */}
            <mesh castShadow receiveShadow>
                <boxGeometry args={[3, 1.8, 0.1]} />
                <meshStandardMaterial color="#111" roughness={0.2} />
            </mesh>
            {/* Screen */}
            <mesh position={[0, 0, 0.06]}>
                <planeGeometry args={[2.8, 1.6]} />
                <meshStandardMaterial 
                    color={isOn ? "#60a5fa" : "#000"} 
                    emissive={isOn ? "#2563eb" : "#000"}
                    emissiveIntensity={isOn ? 1.5 : 0}
                    roughness={0.2}
                    metalness={0.8}
                />
            </mesh>
            {/* Stand */}
            <mesh position={[0, -1.4, 0]} receiveShadow>
                <boxGeometry args={[1.5, 1, 0.8]} />
                 <meshStandardMaterial color="#334155" />
            </mesh>
             {/* Glow Light on Wall */}
            {isOn && (
                <pointLight position={[0, 0, -0.5]} intensity={1} color="#60a5fa" distance={5} />
            )}
        </group>
    );
}

// Heater on Left Wall
const Heater = ({ isOn }: { isOn: boolean }) => {
    return (
        <group position={[-4.8, -1.4, 0]} rotation={[0, Math.PI/2, 0]}>
            {/* Body */}
            <mesh receiveShadow castShadow>
                <boxGeometry args={[2, 0.8, 0.3]} />
                <meshStandardMaterial color="#e2e8f0" />
            </mesh>
            {/* Grills */}
            {Array.from({ length: 8 }).map((_, i) => (
                <mesh key={i} position={[-0.7 + i * 0.2, 0, 0.16]}>
                    <boxGeometry args={[0.1, 0.6, 0.02]} />
                    <meshStandardMaterial color="#94a3b8" />
                </mesh>
            ))}
            {/* Inner Glow */}
            {isOn && (
                <mesh position={[0, 0, 0.1]}>
                     <boxGeometry args={[1.8, 0.6, 0.1]} />
                     <meshBasicMaterial color="#ef4444" />
                </mesh>
            )}
            {/* Light */}
             {isOn && (
                <pointLight position={[0, 0.5, 0.5]} intensity={2} color="#ef4444" distance={3} />
            )}
        </group>
    );
};

const Lights = ({ brightness, color }: { brightness: number, color: string }) => {
  const intensity = (brightness / 100) * 30; // Increased brightness
  return (
    <>
      <pointLight 
        position={[0, 4, 0]} 
        intensity={intensity} 
        color={color} 
        castShadow 
        shadow-bias={-0.0001}
        distance={25}
        decay={2}
      />
      <mesh position={[0, 4.8, 0]}>
         <sphereGeometry args={[0.2]} />
         <meshBasicMaterial color={brightness > 0 ? color : '#333'} />
      </mesh>
      {/* Increased ambient light for better visibility */}
      <ambientLight intensity={0.6} color="#ffffff" />
    </>
  );
};

const SceneContent = ({ roomState }: RoomSceneProps) => {
    const sunlightIntensity = (roomState.blindsPosition / 100) * 2; // Strong sunlight

    return (
        <>
            <PerspectiveCamera makeDefault position={[5, 4, 7]} fov={50} />
            <OrbitControls 
                minPolarAngle={0} 
                maxPolarAngle={Math.PI / 2} 
                enablePan={false}
                minDistance={5}
                maxDistance={15}
            />
            
            <color attach="background" args={[BACKGROUND_COLOR]} />

            <Lights brightness={roomState.brightness} color={roomState.lightColor} />
            
            {/* Sunlight coming from Left (-X) through the window */}
            <directionalLight 
                position={[-10, 5, 0]} 
                intensity={sunlightIntensity} 
                color="#fdfbd3" 
                castShadow
                shadow-bias={-0.001}
            />

            <group>
                <Wall position={[0, 0, -5]} width={10} height={10} depth={0.2} /> {/* Back */}
                <Wall position={[-5, 0, 0]} width={0.2} height={10} depth={10} /> {/* Left */}
                <Wall position={[5, 0, 0]} width={0.2} height={10} depth={10} /> {/* Right */}
                <Wall position={[0, 5, 0]} width={10} height={0.2} depth={10} /> {/* Ceiling */}
                <Floor />
                
                <WindowFrame />
                <Blinds position={roomState.blindsPosition} />
                <Furniture />
                <Thermostat temp={roomState.temperature} target={roomState.targetTemperature} />
                <TV isOn={roomState.isTvOn} />
                <Heater isOn={roomState.isHeaterOn} />
            </group>

            <SoftShadows size={10} samples={10} focus={0.5} />
        </>
    );
};

const RoomScene: React.FC<RoomSceneProps> = ({ roomState }) => {
  return (
    <div className="w-full h-full bg-slate-900">
      <Canvas shadows dpr={[1, 2]}>
        <SceneContent roomState={roomState} />
      </Canvas>
    </div>
  );
};

export default RoomScene;