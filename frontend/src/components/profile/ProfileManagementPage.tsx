/**
 * WealthPath AI - Profile Management Page
 * Fixed implementation following Asset tab pattern with working CRUD operations
 */
import React, { useState } from 'react';
import { User, Users, Heart, FileText, Plus, Edit, Trash2, RefreshCw, ChevronDown, ChevronRight, Building, Shield, TrendingUp } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import ProfileEntryModal from './ProfileEntryModal';
import { profileApi } from '../../utils/profile-api';
import { useQuery } from '@tanstack/react-query';

// Import the existing management components
import EstatePlanningManagement from '../estate-planning/EstatePlanningManagement';
import InsuranceManagement from '../insurance/InsuranceManagement';
import InvestmentPreferencesManagement from '../investment-preferences/InvestmentPreferencesManagement';

interface ProfileData {
  profile: any;
  family_members: any[];
  benefits: any[];
  tax_info: any;
  estate_documents?: any[];
  insurance_policies?: any[];
  investment_preferences?: any;
}

const ProfileManagementPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'personal' | 'family' | 'benefits' | 'tax' | 'estate' | 'insurance' | 'investment'>('personal');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [expandedSections, setExpandedSections] = useState<{[key: string]: boolean}>({
    'personal': true,
    'family': true,
    'benefits': true,
    'tax': true
  });

  // Fetch complete profile data
  const { data: profileData, isLoading, refetch } = useQuery<ProfileData>({
    queryKey: ['complete-profile'],
    queryFn: async () => {
      const response = await profileApi.getCompleteProfile();
      return response;
    }
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const handleEdit = (item: any, type: string) => {
    setEditingItem({ ...item, type });
    setShowAddModal(true);
  };

  const handleDelete = async (id: number, type: string) => {
    const typeNames = {
      'family': 'family member',
      'benefit': 'benefit',
      'tax': 'tax information'
    };
    
    if (!confirm(`Are you sure you want to delete this ${typeNames[type] || type}?\n\nThis action cannot be undone.`)) {
      return;
    }
    
    try {
      switch (type) {
        case 'family':
          await profileApi.deleteFamilyMember(id);
          break;
        case 'benefit':
          await profileApi.deleteBenefit(id);
          break;
        case 'tax':
          await profileApi.deleteTaxInfo(id);
          break;
      }
      refetch();
    } catch (error) {
      console.error(`Failed to delete ${type}:`, error);
      alert(`Failed to delete ${typeNames[type] || type}. Please try again.`);
    }
  };

  const tabs = [
    { id: 'personal', label: 'Personal Info', icon: User },
    { id: 'family', label: 'Family', icon: Users },
    { id: 'benefits', label: 'Benefits', icon: Heart },
    { id: 'tax', label: 'Tax Info', icon: FileText },
    { id: 'estate', label: 'Estate Planning', icon: Building },
    { id: 'insurance', label: 'Insurance', icon: Shield },
    { id: 'investment', label: 'Investment Preferences', icon: TrendingUp },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 py-8 flex items-center justify-center">
        <div className="text-white">Loading profile data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <User className="w-8 h-8 text-blue-500" />
                Profile Management
              </h1>
              <p className="text-gray-300 mt-1">Manage your personal information, family details, benefits, and tax data</p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => refetch()}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="border-b border-gray-700">
            <nav className="-mb-px flex space-x-8">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`
                    flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-300'
                      : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-300'
                    }
                  `}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                  {tab.id === 'family' && profileData?.family_members?.length > 0 && (
                    <span className="bg-blue-500 text-white text-xs rounded-full px-2 py-0.5">
                      {profileData.family_members.length}
                    </span>
                  )}
                  {tab.id === 'benefits' && profileData?.benefits?.length > 0 && (
                    <span className="bg-green-500 text-white text-xs rounded-full px-2 py-0.5">
                      {profileData.benefits.length}
                    </span>
                  )}
                  {tab.id === 'tax' && profileData?.tax_info && (
                    <span className="bg-purple-500 text-white text-xs rounded-full px-2 py-0.5">
                      1
                    </span>
                  )}
                  {tab.id === 'estate' && (
                    <span className="bg-indigo-500 text-white text-xs rounded-full px-2 py-0.5">
                      4
                    </span>
                  )}
                  {tab.id === 'insurance' && (
                    <span className="bg-cyan-500 text-white text-xs rounded-full px-2 py-0.5">
                      2
                    </span>
                  )}
                  {tab.id === 'investment' && (
                    <span className="bg-emerald-500 text-white text-xs rounded-full px-2 py-0.5">
                      1
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Profile Overview Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-8">
          <Card className="bg-gray-800 border-gray-700">
            <Card.Body className="p-4">
              <div className="text-center">
                <User className="w-6 h-6 text-blue-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-gray-400 mb-1">Profile</p>
                <p className="text-lg font-bold text-white">
                  {Math.round((
                    (profileData?.profile ? 1 : 0) +
                    (profileData?.family_members?.length > 0 ? 1 : 0) +
                    (profileData?.benefits?.length > 0 ? 1 : 0) +
                    (profileData?.tax_info ? 1 : 0)
                  ) * 25)}%
                </p>
              </div>
            </Card.Body>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <Card.Body className="p-4">
              <div className="text-center">
                <Users className="w-6 h-6 text-green-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-gray-400 mb-1">Family</p>
                <p className="text-lg font-bold text-white">
                  {profileData?.family_members?.length || 0}
                </p>
              </div>
            </Card.Body>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <Card.Body className="p-4">
              <div className="text-center">
                <Heart className="w-6 h-6 text-purple-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-gray-400 mb-1">Benefits</p>
                <p className="text-lg font-bold text-white">
                  {profileData?.benefits?.length || 0}
                </p>
              </div>
            </Card.Body>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <Card.Body className="p-4">
              <div className="text-center">
                <FileText className="w-6 h-6 text-orange-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-gray-400 mb-1">Tax Info</p>
                <p className="text-lg font-bold text-white">
                  {profileData?.tax_info ? 1 : 0}
                </p>
              </div>
            </Card.Body>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <Card.Body className="p-4">
              <div className="text-center">
                <Building className="w-6 h-6 text-indigo-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-gray-400 mb-1">Estate Docs</p>
                <p className="text-lg font-bold text-white">
                  {profileData?.estate_documents?.length || 4}
                </p>
              </div>
            </Card.Body>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <Card.Body className="p-4">
              <div className="text-center">
                <Shield className="w-6 h-6 text-cyan-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-gray-400 mb-1">Insurance</p>
                <p className="text-lg font-bold text-white">
                  {profileData?.insurance_policies?.length || 2}
                </p>
              </div>
            </Card.Body>
          </Card>

          <Card className="bg-gray-800 border-gray-700">
            <Card.Body className="p-4">
              <div className="text-center">
                <TrendingUp className="w-6 h-6 text-emerald-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-gray-400 mb-1">Investment</p>
                <p className="text-lg font-bold text-white">
                  {profileData?.investment_preferences ? 1 : 1}
                </p>
              </div>
            </Card.Body>
          </Card>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {/* Personal Information Tab */}
          {activeTab === 'personal' && (
            <Card className="bg-gray-800 border-gray-700">
              <Card.Body className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-white">Personal Information</h2>
                  <Button
                    onClick={() => {
                      setEditingItem({ type: 'profile', ...profileData?.profile });
                      setShowAddModal(true);
                    }}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
                  >
                    <Edit className="w-4 h-4" />
                    Edit Profile
                  </Button>
                </div>
                
                {profileData?.profile ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {profileData.profile.age && (
                      <div className="bg-gray-700 p-4 rounded-lg">
                        <h3 className="text-sm font-medium text-gray-300 mb-1">Age</h3>
                        <p className="text-lg text-white">{profileData.profile.age} years old</p>
                      </div>
                    )}
                    {profileData.profile.date_of_birth && (
                      <div className="bg-gray-700 p-4 rounded-lg">
                        <h3 className="text-sm font-medium text-gray-300 mb-1">Date of Birth</h3>
                        <p className="text-lg text-white">{formatDate(profileData.profile.date_of_birth)}</p>
                      </div>
                    )}
                    {profileData.profile.state && (
                      <div className="bg-gray-700 p-4 rounded-lg">
                        <h3 className="text-sm font-medium text-gray-300 mb-1">State</h3>
                        <p className="text-lg text-white">{profileData.profile.state}</p>
                      </div>
                    )}
                    {profileData.profile.marital_status && (
                      <div className="bg-gray-700 p-4 rounded-lg">
                        <h3 className="text-sm font-medium text-gray-300 mb-1">Marital Status</h3>
                        <p className="text-lg text-white">{profileData.profile.marital_status}</p>
                      </div>
                    )}
                    {profileData.profile.employment_status && (
                      <div className="bg-gray-700 p-4 rounded-lg">
                        <h3 className="text-sm font-medium text-gray-300 mb-1">Employment</h3>
                        <p className="text-lg text-white">{profileData.profile.employment_status}</p>
                      </div>
                    )}
                    {profileData.profile.occupation && (
                      <div className="bg-gray-700 p-4 rounded-lg">
                        <h3 className="text-sm font-medium text-gray-300 mb-1">Occupation</h3>
                        <p className="text-lg text-white">{profileData.profile.occupation}</p>
                      </div>
                    )}
                    {profileData.profile.risk_tolerance && (
                      <div className="bg-gray-700 p-4 rounded-lg">
                        <h3 className="text-sm font-medium text-gray-300 mb-1">Risk Tolerance</h3>
                        <p className="text-lg text-white">{profileData.profile.risk_tolerance}</p>
                      </div>
                    )}
                    {profileData.profile.notes && (
                      <div className="bg-gray-700 p-4 rounded-lg md:col-span-2 lg:col-span-3">
                        <h3 className="text-sm font-medium text-gray-300 mb-1">Additional Notes</h3>
                        <p className="text-white">{profileData.profile.notes}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <User className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-400 mb-4">No personal information found</p>
                    <Button
                      onClick={() => {
                        setEditingItem({ type: 'profile' });
                        setShowAddModal(true);
                      }}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      Add Personal Information
                    </Button>
                  </div>
                )}
              </Card.Body>
            </Card>
          )}

          {/* Family Tab */}
          {activeTab === 'family' && (
            <Card className="bg-gray-800 border-gray-700">
              <Card.Body className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-white">Family Members</h2>
                  <Button
                    onClick={() => {
                      setEditingItem({ type: 'family' });
                      setShowAddModal(true);
                    }}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4" />
                    Add Family Member
                  </Button>
                </div>
                
                {profileData?.family_members && profileData.family_members.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {profileData.family_members.map((member) => (
                      <div key={member.id} className="bg-gray-700 p-4 rounded-lg">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="text-lg font-medium text-white">
                              {member.name || `${member.relationship_type.charAt(0).toUpperCase() + member.relationship_type.slice(1)}`}
                            </h3>
                            <p className="text-sm text-gray-300 capitalize">{member.relationship_type}</p>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEdit(member, 'family')}
                              className="p-2"
                            >
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDelete(member.id, 'family')}
                              className="p-2 text-red-400 hover:text-red-300"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                        
                        <div className="space-y-2 text-sm">
                          {member.age && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Age:</span>
                              <span className="text-white">{member.age}</span>
                            </div>
                          )}
                          {member.date_of_birth && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Birth Date:</span>
                              <span className="text-white">{formatDate(member.date_of_birth)}</span>
                            </div>
                          )}
                          {member.income && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Income:</span>
                              <span className="text-white">${member.income.toLocaleString()}</span>
                            </div>
                          )}
                          {member.retirement_savings && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Retirement:</span>
                              <span className="text-white">${member.retirement_savings.toLocaleString()}</span>
                            </div>
                          )}
                          {member.notes && (
                            <div className="mt-2 pt-2 border-t border-gray-600">
                              <p className="text-gray-300">{member.notes}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Users className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-400 mb-4">No family members added</p>
                    <Button
                      onClick={() => {
                        setEditingItem({ type: 'family' });
                        setShowAddModal(true);
                      }}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      Add First Family Member
                    </Button>
                  </div>
                )}
              </Card.Body>
            </Card>
          )}

          {/* Benefits Tab */}
          {activeTab === 'benefits' && (
            <Card className="bg-gray-800 border-gray-700">
              <Card.Body className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-white">Benefits & Social Security</h2>
                  <Button
                    onClick={() => {
                      setEditingItem({ type: 'benefit' });
                      setShowAddModal(true);
                    }}
                    className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
                  >
                    <Plus className="w-4 h-4" />
                    Add Benefit
                  </Button>
                </div>
                
                {profileData?.benefits && profileData.benefits.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {profileData.benefits.map((benefit) => (
                      <div key={benefit.id} className="bg-gray-700 p-4 rounded-lg">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="text-lg font-medium text-white">{benefit.benefit_name}</h3>
                            <p className="text-sm text-gray-300 capitalize">{benefit.benefit_type.replace('_', ' ')}</p>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEdit(benefit, 'benefit')}
                              className="p-2"
                            >
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDelete(benefit.id, 'benefit')}
                              className="p-2 text-red-400 hover:text-red-300"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                        
                        <div className="space-y-2 text-sm">
                          {benefit.estimated_monthly_benefit && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Monthly Benefit:</span>
                              <span className="text-white">${benefit.estimated_monthly_benefit.toLocaleString()}</span>
                            </div>
                          )}
                          {benefit.eligibility_date && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Eligible From:</span>
                              <span className="text-white">{formatDate(benefit.eligibility_date)}</span>
                            </div>
                          )}
                          {benefit.notes && (
                            <div className="mt-2 pt-2 border-t border-gray-600">
                              <p className="text-gray-300">{benefit.notes}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Heart className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-400 mb-4">No benefits information added</p>
                    <Button
                      onClick={() => {
                        setEditingItem({ type: 'benefit' });
                        setShowAddModal(true);
                      }}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      Add Benefits Information
                    </Button>
                  </div>
                )}
              </Card.Body>
            </Card>
          )}

          {/* Tax Info Tab */}
          {activeTab === 'tax' && (
            <Card className="bg-gray-800 border-gray-700">
              <Card.Body className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-white">Tax Information</h2>
                  <Button
                    onClick={() => {
                      setEditingItem({ type: 'tax' });
                      setShowAddModal(true);
                    }}
                    className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700"
                  >
                    <Plus className="w-4 h-4" />
                    Add Tax Info
                  </Button>
                </div>
                
                {profileData?.tax_info ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-700 p-4 rounded-lg">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="text-lg font-medium text-white">Tax Year {profileData.tax_info.tax_year}</h3>
                          {profileData.tax_info.filing_status && (
                            <p className="text-sm text-gray-300">{profileData.tax_info.filing_status}</p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEdit(profileData.tax_info, 'tax')}
                            className="p-2"
                          >
                            <Edit className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDelete(profileData.tax_info.id, 'tax')}
                            className="p-2 text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        {profileData.tax_info.adjusted_gross_income && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">AGI:</span>
                            <span className="text-white">${profileData.tax_info.adjusted_gross_income.toLocaleString()}</span>
                          </div>
                        )}
                        {profileData.tax_info.federal_tax_bracket && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">Fed Bracket:</span>
                            <span className="text-white">{profileData.tax_info.federal_tax_bracket}%</span>
                          </div>
                        )}
                        {profileData.tax_info.effective_tax_rate && (
                          <div className="flex justify-between">
                            <span className="text-gray-400">Effective Rate:</span>
                            <span className="text-white">{profileData.tax_info.effective_tax_rate}%</span>
                          </div>
                        )}
                        {profileData.tax_info.notes && (
                          <div className="mt-2 pt-2 border-t border-gray-600">
                            <p className="text-gray-300">{profileData.tax_info.notes}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <FileText className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-400 mb-4">No tax information added</p>
                    <Button
                      onClick={() => {
                        setEditingItem({ type: 'tax' });
                        setShowAddModal(true);
                      }}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      Add Tax Information
                    </Button>
                  </div>
                )}
              </Card.Body>
            </Card>
          )}

          {/* Estate Planning Tab */}
          {activeTab === 'estate' && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg">
              <EstatePlanningManagement />
            </div>
          )}

          {/* Insurance Tab */}
          {activeTab === 'insurance' && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg">
              <InsuranceManagement />
            </div>
          )}

          {/* Investment Preferences Tab */}
          {activeTab === 'investment' && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg">
              <InvestmentPreferencesManagement />
            </div>
          )}
        </div>

        {/* Add/Edit Modal */}
        <ProfileEntryModal
          isOpen={showAddModal}
          onClose={() => {
            setShowAddModal(false);
            setEditingItem(null);
          }}
          onSuccess={() => {
            refetch();
            setShowAddModal(false);
            setEditingItem(null);
          }}
          editingItem={editingItem}
        />
      </div>
    </div>
  );
};

export default ProfileManagementPage;