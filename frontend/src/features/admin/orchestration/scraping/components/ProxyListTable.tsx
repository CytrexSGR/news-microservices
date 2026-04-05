import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import {
  useProxyList,
  useProxyStats,
  useAddProxy,
  useRemoveProxy,
  useTestProxy,
  useRotateProxy,
  useEnableProxy,
  useDisableProxy,
} from '../api';
import type { ProxyInfo, ProxyStatus, ProxyType } from '../types/scraping.types';

interface ProxyListTableProps {
  className?: string;
}

/**
 * Status Badge
 */
const StatusBadge: React.FC<{ status: ProxyStatus }> = ({ status }) => {
  const colors: Record<ProxyStatus, string> = {
    healthy: 'bg-green-100 text-green-800',
    unhealthy: 'bg-red-100 text-red-800',
    unknown: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status]}`}>
      {status.toUpperCase()}
    </span>
  );
};

/**
 * Add Proxy Modal
 */
const AddProxyModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { host: string; port: number; type: ProxyType; username?: string; password?: string }) => void;
  isLoading: boolean;
}> = ({ isOpen, onClose, onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    host: '',
    port: 8080,
    type: 'http' as ProxyType,
    username: '',
    password: '',
  });

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      host: formData.host,
      port: formData.port,
      type: formData.type,
      username: formData.username || undefined,
      password: formData.password || undefined,
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">Add Proxy</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Host *</label>
            <input
              type="text"
              value={formData.host}
              onChange={(e) => setFormData((f) => ({ ...f, host: e.target.value }))}
              placeholder="192.168.1.100"
              required
              className="w-full px-3 py-2 border rounded"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Port *</label>
              <input
                type="number"
                value={formData.port}
                onChange={(e) => setFormData((f) => ({ ...f, port: parseInt(e.target.value) }))}
                min={1}
                max={65535}
                required
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Type</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData((f) => ({ ...f, type: e.target.value as ProxyType }))}
                className="w-full px-3 py-2 border rounded"
              >
                <option value="http">HTTP</option>
                <option value="https">HTTPS</option>
                <option value="socks5">SOCKS5</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Username</label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData((f) => ({ ...f, username: e.target.value }))}
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Password</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData((f) => ({ ...f, password: e.target.value }))}
                className="w-full px-3 py-2 border rounded"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !formData.host}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {isLoading ? 'Adding...' : 'Add Proxy'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

/**
 * Proxy List Table
 *
 * Displays proxy pool with management actions.
 */
export const ProxyListTable: React.FC<ProxyListTableProps> = ({ className }) => {
  const [showAddModal, setShowAddModal] = useState(false);

  const { data: stats } = useProxyStats();
  const { data, isLoading, error, refetch, isRefetching } = useProxyList();

  const addProxy = useAddProxy();
  const removeProxy = useRemoveProxy();
  const testProxy = useTestProxy();
  const rotateProxy = useRotateProxy();
  const enableProxy = useEnableProxy();
  const disableProxy = useDisableProxy();

  const handleAddProxy = async (proxyData: {
    host: string;
    port: number;
    type: ProxyType;
    username?: string;
    password?: string;
  }) => {
    try {
      await addProxy.mutateAsync(proxyData);
      setShowAddModal(false);
    } catch (err) {
      console.error('Failed to add proxy:', err);
    }
  };

  const handleRemove = async (proxyId: string) => {
    if (!confirm('Remove this proxy?')) return;
    try {
      await removeProxy.mutateAsync(proxyId);
    } catch (err) {
      console.error('Failed to remove proxy:', err);
    }
  };

  const handleTest = async (proxyId: string) => {
    try {
      const result = await testProxy.mutateAsync(proxyId);
      alert(
        result.success
          ? `Proxy working!\nResponse time: ${result.response_time_ms}ms\nExternal IP: ${result.external_ip || 'N/A'}`
          : `Proxy test failed: ${result.error}`
      );
      refetch();
    } catch (err) {
      console.error('Failed to test proxy:', err);
    }
  };

  const handleRotate = async () => {
    try {
      const result = await rotateProxy.mutateAsync(undefined);
      alert(`Rotated to proxy ${result.new_proxy_id}`);
      refetch();
    } catch (err) {
      console.error('Failed to rotate proxy:', err);
    }
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString();
  };

  if (error) {
    return (
      <Card className={className}>
        <div className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-600">Proxy Pool</h3>
          <p className="text-sm text-red-500 mb-4">
            Failed to load proxies: {error.message}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card className={className}>
        <div className="p-6">
          {/* Header with Stats */}
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-semibold">Proxy Pool</h3>
              {stats && (
                <p className="text-sm text-gray-500">
                  {stats.healthy}/{stats.total} healthy |{' '}
                  {(stats.overall_success_rate * 100).toFixed(1)}% success rate
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowAddModal(true)}
                className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
              >
                Add Proxy
              </button>
              <button
                onClick={handleRotate}
                disabled={rotateProxy.isPending}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
              >
                Rotate
              </button>
              <button
                onClick={() => refetch()}
                disabled={isRefetching}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
              >
                {isRefetching ? 'Loading...' : 'Refresh'}
              </button>
            </div>
          </div>

          {/* Table */}
          {isLoading ? (
            <div className="animate-pulse space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-100 rounded"></div>
              ))}
            </div>
          ) : data?.proxies.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No proxies configured</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left">Host:Port</th>
                    <th className="px-3 py-2 text-left">Type</th>
                    <th className="px-3 py-2 text-left">Status</th>
                    <th className="px-3 py-2 text-left">Success Rate</th>
                    <th className="px-3 py-2 text-left">Avg Response</th>
                    <th className="px-3 py-2 text-left">Requests</th>
                    <th className="px-3 py-2 text-left">Last Checked</th>
                    <th className="px-3 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data?.proxies.map((proxy) => (
                    <tr key={proxy.proxy_id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-mono">
                        {proxy.host}:{proxy.port}
                        {proxy.auth_required && (
                          <span className="ml-1 text-xs text-gray-500">(auth)</span>
                        )}
                      </td>
                      <td className="px-3 py-2 uppercase text-xs">{proxy.type}</td>
                      <td className="px-3 py-2">
                        <StatusBadge status={proxy.status} />
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={
                            proxy.success_rate >= 0.9
                              ? 'text-green-600'
                              : proxy.success_rate >= 0.7
                              ? 'text-yellow-600'
                              : 'text-red-600'
                          }
                        >
                          {(proxy.success_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-3 py-2 text-gray-600">
                        {proxy.avg_response_time_ms}ms
                      </td>
                      <td className="px-3 py-2">{proxy.total_requests.toLocaleString()}</td>
                      <td className="px-3 py-2 text-xs text-gray-500">
                        {formatDate(proxy.last_checked)}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleTest(proxy.proxy_id)}
                            disabled={testProxy.isPending}
                            className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                          >
                            Test
                          </button>
                          <button
                            onClick={() => handleRemove(proxy.proxy_id)}
                            disabled={removeProxy.isPending}
                            className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>

      <AddProxyModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleAddProxy}
        isLoading={addProxy.isPending}
      />
    </>
  );
};
