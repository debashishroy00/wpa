/**
 * Estate Planning Management Component
 * Comprehensive estate planning document tracking and management
 */
import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Plus, 
  Edit, 
  Trash2, 
  Calendar, 
  User, 
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Users,
  Building,
  Heart,
  Scale,
  AlertCircle
} from 'lucide-react';

import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { apiClient } from '../../utils/api-simple';

interface EstatePlanningDocument {
  id: string;
  document_type: string;
  document_name: string;
  status: string;
  last_updated?: string;
  next_review_date?: string;
  attorney_contact?: string;
  document_location?: string;
  document_details?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface EstatePlanningSummary {
  total_documents: number;
  documents_by_status: Record<string, {
    count: number;
    documents: Array<{
      id: string;
      name: string;
      type: string;
    }>;
  }>;
  documents_by_type: Record<string, {
    count: number;
    documents: Array<{
      id: string;
      name: string;
      status: string;
    }>;
  }>;
  documents: EstatePlanningDocument[];
  upcoming_reviews: EstatePlanningDocument[];
  gaps_identified: string[];
}

interface DocumentFormData {
  document_type: string;
  document_name: string;
  status: string;
  last_updated: string;
  next_review_date: string;
  attorney_contact: string;
  document_location: string;
}

// Document type configuration
const DOCUMENT_TYPE_CONFIG = {
  will: { label: 'Will', icon: FileText, color: 'text-blue-500' },
  trust: { label: 'Trust', icon: Shield, color: 'text-green-500' },
  power_of_attorney: { label: 'Power of Attorney', icon: Users, color: 'text-purple-500' },
  healthcare_directive: { label: 'Healthcare Directive', icon: Heart, color: 'text-red-500' },
  beneficiary_designation: { label: 'Beneficiary Designations', icon: User, color: 'text-orange-500' }
};

const STATUS_CONFIG = {
  current: { label: 'Current', color: 'bg-green-500', textColor: 'text-green-500' },
  needs_update: { label: 'Needs Update', color: 'bg-yellow-500', textColor: 'text-yellow-500' },
  missing: { label: 'Missing', color: 'bg-red-500', textColor: 'text-red-500' },
  in_progress: { label: 'In Progress', color: 'bg-blue-500', textColor: 'text-blue-500' }
};

const EstatePlanningManagement: React.FC = () => {
  const [documents, setDocuments] = useState<EstatePlanningDocument[]>([]);
  const [summary, setSummary] = useState<EstatePlanningSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingDocument, setEditingDocument] = useState<EstatePlanningDocument | null>(null);
  const [formData, setFormData] = useState<DocumentFormData>({
    document_type: 'will',
    document_name: '',
    status: 'current',
    last_updated: '',
    next_review_date: '',
    attorney_contact: '',
    document_location: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [documentTypes, setDocumentTypes] = useState<Array<{value: string; label: string; description: string}>>([]);

  useEffect(() => {
    loadEstatePlanningData();
    fetchDocumentTypes();
  }, []);

  const fetchDocumentTypes = async () => {
    try {
      const response = await apiClient.get('/api/v1/estate-planning/document-types');
      setDocumentTypes(response.document_types || []);
    } catch (error) {
      console.error('Failed to fetch document types:', error);
    }
  };

  const loadEstatePlanningData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [documentsResponse, summaryResponse] = await Promise.all([
        apiClient.get('/api/v1/estate-planning/documents'),
        apiClient.get('/api/v1/estate-planning/summary')
      ]);

      setDocuments(documentsResponse || []);
      setSummary(summaryResponse || null);
    } catch (err) {
      console.error('Failed to load estate planning data:', err);
      setError('Failed to load estate planning data');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this estate planning document?')) {
      return;
    }

    try {
      await apiClient.delete(`/api/v1/estate-planning/documents/${documentId}`);
      await loadEstatePlanningData();
    } catch (err) {
      console.error('Failed to delete document:', err);
      setError('Failed to delete document');
    }
  };

  const resetForm = () => {
    setFormData({
      document_type: 'will',
      document_name: '',
      status: 'current',
      last_updated: '',
      next_review_date: '',
      attorney_contact: '',
      document_location: ''
    });
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.document_name.trim()) {
      setError('Document name is required');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        document_type: formData.document_type,
        document_name: formData.document_name.trim(),
        status: formData.status,
        last_updated: formData.last_updated ? formData.last_updated : undefined,
        next_review_date: formData.next_review_date ? formData.next_review_date : undefined,
        attorney_contact: formData.attorney_contact.trim() || undefined,
        document_location: formData.document_location.trim() || undefined,
        document_details: {}
      };

      if (editingDocument) {
        await apiClient.put(`/api/v1/estate-planning/documents/${editingDocument.id}`, payload);
        setEditingDocument(null);
      } else {
        await apiClient.post('/api/v1/estate-planning/documents', payload);
        setShowAddModal(false);
      }

      resetForm();
      await loadEstatePlanningData();
    } catch (error: any) {
      console.error('Failed to save document:', error);
      setError(error.response?.data?.detail || 'Failed to save document');
    } finally {
      setSubmitting(false);
    }
  };

  const openEditModal = (document: EstatePlanningDocument) => {
    setFormData({
      document_type: document.document_type,
      document_name: document.document_name,
      status: document.status,
      last_updated: document.last_updated?.split('T')[0] || '',
      next_review_date: document.next_review_date?.split('T')[0] || '',
      attorney_contact: document.attorney_contact || '',
      document_location: document.document_location || ''
    });
    setEditingDocument(document);
    setError(null);
  };

  const openAddModal = () => {
    resetForm();
    setShowAddModal(true);
    setError(null);
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString();
  };

  const getDocumentTypeIcon = (documentType: string) => {
    return DOCUMENT_TYPE_CONFIG[documentType as keyof typeof DOCUMENT_TYPE_CONFIG]?.icon || FileText;
  };

  const getDocumentTypeColor = (documentType: string) => {
    return DOCUMENT_TYPE_CONFIG[documentType as keyof typeof DOCUMENT_TYPE_CONFIG]?.color || 'text-gray-500';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'current': return CheckCircle;
      case 'needs_update': return AlertTriangle;
      case 'missing': return AlertCircle;
      case 'in_progress': return Clock;
      default: return FileText;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-white">Loading estate planning data...</div>
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <Card.Body>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">Total Documents</p>
                <p className="text-2xl font-bold text-white">
                  {summary?.total_documents || 0}
                </p>
              </div>
              <FileText className="w-8 h-8 text-blue-500" />
            </div>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">Current</p>
                <p className="text-2xl font-bold text-white">
                  {summary?.documents_by_status?.current?.count || 0}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">Need Updates</p>
                <p className="text-2xl font-bold text-white">
                  {(summary?.documents_by_status?.needs_update?.count || 0) + 
                   (summary?.documents_by_status?.missing?.count || 0)}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-500" />
            </div>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">Reviews Due</p>
                <p className="text-2xl font-bold text-white">
                  {summary?.upcoming_reviews?.length || 0}
                </p>
              </div>
              <Calendar className="w-8 h-8 text-purple-500" />
            </div>
          </Card.Body>
        </Card>
      </div>

      {/* Gaps Identified */}
      {summary?.gaps_identified && summary.gaps_identified.length > 0 && (
        <Card>
          <Card.Header>
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              <h3 className="text-lg font-semibold text-white">Estate Planning Gaps</h3>
            </div>
          </Card.Header>
          <Card.Body>
            <div className="space-y-2">
              {summary.gaps_identified.map((gap, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span className="text-gray-200">{gap}</span>
                </div>
              ))}
            </div>
          </Card.Body>
        </Card>
      )}

      {/* Main Estate Planning Documents */}
      <Card>
        <Card.Header>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Estate Planning Documents</h3>
            <Button onClick={openAddModal}>
              <Plus className="w-4 h-4 mr-2" />
              Add Document
            </Button>
          </div>
        </Card.Header>
        
        <Card.Body>
          {documents.length === 0 ? (
            <div className="text-center py-8">
              <Scale className="w-16 h-16 text-gray-500 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-white mb-2">No Estate Planning Documents</h4>
              <p className="text-gray-400 mb-6">Start protecting your financial future by adding your estate planning documents</p>
              <Button onClick={openAddModal}>
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Document
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Group documents by type */}
              {Object.entries(summary?.documents_by_type || {}).map(([documentType, typeData]) => {
                const Icon = getDocumentTypeIcon(documentType);
                const config = DOCUMENT_TYPE_CONFIG[documentType as keyof typeof DOCUMENT_TYPE_CONFIG];
                const typeDocuments = documents.filter(d => d.document_type === documentType);
                
                return (
                  <div key={documentType} className="border border-gray-700 rounded-lg p-4 bg-gray-800">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <Icon className={`w-6 h-6 ${getDocumentTypeColor(documentType)}`} />
                        <div>
                          <h4 className="font-medium text-white">{config?.label}</h4>
                          <p className="text-sm text-white">
                            {typeData.count} documents
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {typeDocuments.map((document) => {
                        const StatusIcon = getStatusIcon(document.status);
                        const statusConfig = STATUS_CONFIG[document.status as keyof typeof STATUS_CONFIG];
                        
                        return (
                          <div key={document.id} className="bg-gray-800 border border-gray-700 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <h5 className="font-medium text-white">{document.document_name}</h5>
                              <div className="flex items-center space-x-1">
                                <button
                                  onClick={() => openEditModal(document)}
                                  className="p-1 text-gray-300 hover:text-white transition-colors"
                                >
                                  <Edit className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => handleDeleteDocument(document.id)}
                                  className="p-1 text-gray-300 hover:text-white transition-colors"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                            
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <StatusIcon className={`w-4 h-4 ${statusConfig?.textColor || 'text-gray-400'}`} />
                                <span className={`text-sm ${statusConfig?.textColor || 'text-gray-400'}`}>
                                  {statusConfig?.label || document.status}
                                </span>
                              </div>
                              
                              {document.last_updated && (
                                <div>
                                  <p className="text-white">Last Updated</p>
                                  <p className="font-medium text-white">{formatDate(document.last_updated)}</p>
                                </div>
                              )}
                              
                              {document.next_review_date && (
                                <div>
                                  <p className="text-white">Next Review</p>
                                  <p className="font-medium text-white">{formatDate(document.next_review_date)}</p>
                                </div>
                              )}
                              
                              {document.attorney_contact && (
                                <div>
                                  <p className="text-white">Attorney</p>
                                  <p className="font-medium text-white">{document.attorney_contact}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Document Form Modal (Add/Edit) */}
      {(showAddModal || editingDocument) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {editingDocument ? 'Edit Estate Planning Document' : 'Add Estate Planning Document'}
            </h3>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type *
                </label>
                <select
                  value={formData.document_type}
                  onChange={(e) => setFormData({...formData, document_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  {documentTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Name *
                </label>
                <input
                  type="text"
                  value={formData.document_name}
                  onChange={(e) => setFormData({...formData, document_name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Last Will and Testament"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status *
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({...formData, status: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="current">Current</option>
                  <option value="needs_update">Needs Update</option>
                  <option value="missing">Missing</option>
                  <option value="in_progress">In Progress</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Last Updated
                </label>
                <input
                  type="date"
                  value={formData.last_updated}
                  onChange={(e) => setFormData({...formData, last_updated: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Next Review Date
                </label>
                <input
                  type="date"
                  value={formData.next_review_date}
                  onChange={(e) => setFormData({...formData, next_review_date: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Attorney Contact
                </label>
                <input
                  type="text"
                  value={formData.attorney_contact}
                  onChange={(e) => setFormData({...formData, attorney_contact: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Attorney name and contact info"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Location
                </label>
                <input
                  type="text"
                  value={formData.document_location}
                  onChange={(e) => setFormData({...formData, document_location: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Physical or digital storage location"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button 
                  type="button"
                  variant="outline" 
                  onClick={() => {
                    setShowAddModal(false);
                    setEditingDocument(null);
                  }}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit"
                  disabled={submitting}
                >
                  {submitting ? (editingDocument ? 'Updating...' : 'Saving...') : (editingDocument ? 'Update Document' : 'Save Document')}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default EstatePlanningManagement;