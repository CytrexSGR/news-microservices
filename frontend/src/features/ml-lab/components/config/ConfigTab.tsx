/**
 * ML Lab Config Tab
 *
 * Configure gate thresholds and enable/disable gates.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Switch } from '@/components/ui/Switch';
import { Settings2, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

import { gateConfigApi } from '../../api/mlLabApi';
import { MLArea, type GateConfig } from '../../types';
import { AREA_ICONS, AREA_DESCRIPTIONS } from '../../utils/constants';

export function ConfigTab() {
  const [configs, setConfigs] = useState<GateConfig[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchConfigs = useCallback(async () => {
    try {
      const data = await gateConfigApi.list();
      setConfigs(data.configs);
    } catch (error) {
      console.error('Failed to fetch configs:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfigs();
  }, [fetchConfigs]);

  const handleToggle = async (area: MLArea, enabled: boolean) => {
    try {
      await gateConfigApi.update(area, { enabled });
      toast.success(`${area} gate ${enabled ? 'enabled' : 'disabled'}`);
      fetchConfigs();
    } catch (error) {
      toast.error('Failed to update config');
    }
  };

  const handleThresholdChange = async (area: MLArea, threshold: number) => {
    try {
      await gateConfigApi.update(area, { confidence_threshold: threshold });
      toast.success('Threshold updated');
      fetchConfigs();
    } catch (error) {
      toast.error('Failed to update threshold');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings2 className="h-5 w-5" />
            Gate Configuration
          </CardTitle>
          <CardDescription>
            Configure which gates are active and their confidence thresholds
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {configs.map((config) => (
              <div
                key={config.area}
                className="flex items-center justify-between p-4 bg-muted rounded-lg"
              >
                <div className="flex items-center gap-4">
                  {AREA_ICONS[config.area]}
                  <div>
                    <p className="font-medium capitalize">{config.area} Gate</p>
                    <p className="text-sm text-muted-foreground">
                      {AREA_DESCRIPTIONS[config.area]}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-muted-foreground">Threshold:</label>
                    <Input
                      type="number"
                      value={config.confidence_threshold}
                      onChange={(e) =>
                        handleThresholdChange(config.area, parseFloat(e.target.value) || 0.5)
                      }
                      className="w-20"
                      min={0}
                      max={1}
                      step={0.05}
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <label className="text-sm text-muted-foreground">Enabled:</label>
                    <Switch
                      checked={config.enabled}
                      onCheckedChange={(checked) => handleToggle(config.area, checked)}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ConfigTab;
