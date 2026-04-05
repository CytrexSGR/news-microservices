import { GlobeViewer } from '../components/GlobeViewer';
import { GlobeControls } from '../components/GlobeControls';

export function GlobePage() {
  return (
    <div className="relative w-full h-[calc(100vh-64px)]">
      <GlobeViewer />
      <GlobeControls />
    </div>
  );
}
