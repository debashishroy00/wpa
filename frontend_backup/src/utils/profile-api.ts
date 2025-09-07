/**
 * WealthPath AI - Profile API Utilities
 * API utilities for user profile, family, benefits, and tax information
 */
import { apiClient } from './api-simple';

// Profile API endpoints
export const profileApi = {
  // User Profile
  getProfile: async () => {
    try {
      const response = await apiClient.get('/api/v1/profile/profile');
      console.log('📱 Profile API response:', response);
      return response || null;
    } catch (error) {
      console.error('❌ Profile API error:', error);
      return null;
    }
  },

  createOrUpdateProfile: async (data: any) => {
    try {
      const response = await apiClient.post('/api/v1/profile/profile', data);
      return response || null;
    } catch (error) {
      console.error('❌ Create profile error:', error);
      throw error;
    }
  },

  updateProfile: async (data: any) => {
    try {
      const response = await apiClient.patch('/api/v1/profile/profile', data);
      return response || null;
    } catch (error) {
      console.error('❌ Update profile error:', error);
      throw error;
    }
  },

  // Family Members
  getFamilyMembers: async () => {
    try {
      const response = await apiClient.get('/api/v1/profile/family');
      return response || [];
    } catch (error) {
      console.error('❌ Family members API error:', error);
      return [];
    }
  },

  addFamilyMember: async (data: any) => {
    const response = await apiClient.post('/api/v1/profile/family', data);
    return response;
  },

  updateFamilyMember: async (id: number, data: any) => {
    const response = await apiClient.patch(`/api/v1/profile/family/${id}`, data);
    return response;
  },

  deleteFamilyMember: async (id: number) => {
    const response = await apiClient.delete(`/api/v1/profile/family/${id}`);
    return response;
  },

  // Benefits
  getBenefits: async () => {
    const response = await apiClient.get('/api/v1/profile/benefits');
    return response;
  },

  addBenefit: async (data: any) => {
    const response = await apiClient.post('/api/v1/profile/benefits', data);
    return response;
  },

  updateBenefit: async (id: number, data: any) => {
    const response = await apiClient.patch(`/api/v1/profile/benefits/${id}`, data);
    return response;
  },

  deleteBenefit: async (id: number) => {
    const response = await apiClient.delete(`/api/v1/profile/benefits/${id}`);
    return response;
  },

  // Tax Info
  getTaxInfo: async (taxYear?: number) => {
    const params = taxYear ? { tax_year: taxYear } : {};
    const response = await apiClient.get('/api/v1/profile/tax-info', { params });
    return response;
  },

  addTaxInfo: async (data: any) => {
    const response = await apiClient.post('/api/v1/profile/tax-info', data);
    return response;
  },

  updateTaxInfo: async (id: number, data: any) => {
    const response = await apiClient.patch(`/api/v1/profile/tax-info/${id}`, data);
    return response;
  },

  deleteTaxInfo: async (id: number) => {
    const response = await apiClient.delete(`/api/v1/profile/tax-info/${id}`);
    return response;
  },

  // Complete Profile
  getCompleteProfile: async () => {
    const response = await apiClient.get('/api/v1/profile/complete-profile');
    return response;
  },

  // Helper: Create entry based on category
  createEntry: async (data: any) => {
    const { category, subcategory, description, notes } = data;
    
    console.log('🔍 PROFILE API DEBUG - Entry data received:', {
      category,
      subcategory, 
      description,
      notes,
      fullData: data
    });
    
    // Route to appropriate endpoint based on category
    switch (category) {
      case 'profile':
        // Parse the notes field to extract structured data
        const value = notes || '';
        
        console.log('🔍 Checking spouse routing conditions:');
        console.log('  - subcategory === "Spouse/Partner":', subcategory === 'Spouse/Partner');
        console.log('  - subcategory includes "Spouse":', subcategory && subcategory.toLowerCase().includes('spouse'));
        console.log('  - description includes "spouse":', description.toLowerCase().includes('spouse'));
        
        // Check if this is spouse/family related first
        if (subcategory === 'Spouse/Partner' || 
            (subcategory && subcategory.toLowerCase().includes('spouse')) || 
            description.toLowerCase().includes('spouse') ||
            subcategory === 'Dependents' ||
            (subcategory && subcategory.toLowerCase().includes('dependent')) ||
            description.toLowerCase().includes('child') ||
            description.toLowerCase().includes('dependent')) {
          
          console.log('✅ ROUTING TO FAMILY MEMBER API - Family entry detected');
          console.log('🔍 Entry type determined by:', { subcategory, description });
          
          // Determine relationship type
          let relationshipType = 'spouse'; // default
          if (subcategory === 'Dependents' || 
              (subcategory && subcategory.toLowerCase().includes('dependent')) ||
              description.toLowerCase().includes('child') ||
              description.toLowerCase().includes('dependent')) {
            relationshipType = 'child';
          }
          
          // Create family member data
          let familyData: any = {
            relationship_type: relationshipType,
            name: description.toLowerCase().includes('spouse') ? 'Spouse' : 
                  description.toLowerCase().includes('child') ? 'Child' : undefined
          };
          
          // Handle composite descriptions like "Name, Age"
          if (description.toLowerCase().includes('name') && description.toLowerCase().includes('age')) {
            // This is a combined name and age entry - parse the value
            console.log('🔍 Parsing combined name and age entry:', value);
            
            // Try to extract name and age from the value
            // Assuming format like "John, 45" or "John 45" or "45 John"
            const parts = value.split(/[,\s]+/).filter(part => part.trim());
            
            for (const part of parts) {
              const trimmedPart = part.trim();
              const ageNum = parseInt(trimmedPart);
              
              if (!isNaN(ageNum) && ageNum > 0 && ageNum < 120) {
                // This part is the age
                familyData.age = ageNum;
                console.log('📝 Extracted spouse age:', ageNum);
              } else if (trimmedPart && isNaN(parseInt(trimmedPart))) {
                // This part is likely the name
                familyData.name = trimmedPart;
                console.log('📝 Extracted spouse name:', trimmedPart);
              }
            }
            
            // If we couldn't parse it properly, store in notes
            if (!familyData.age && !familyData.name) {
              familyData.notes = `${description}: ${value}`;
            }
          } else if (description.toLowerCase().includes('age')) {
            const age = parseInt(value);
            if (!isNaN(age)) familyData.age = age;
          } else if (description.toLowerCase().includes('name')) {
            familyData.name = value;
          } else if (description.toLowerCase().includes('income')) {
            const income = parseFloat(value);
            if (!isNaN(income)) familyData.income = income;
          } else if (description.toLowerCase().includes('retirement') || description.toLowerCase().includes('savings')) {
            const savings = parseFloat(value);
            if (!isNaN(savings)) familyData.retirement_savings = savings;
          } else {
            familyData.notes = `${description}: ${value}`;
          }
          
          console.log('📤 Creating family member with data:', familyData);
          return profileApi.addFamilyMember(familyData);
        }
        
        // For personal profile data
        let profileData: any = {};
        
        switch (subcategory) {
          case 'Personal Information':
            // Try to parse common profile fields from description and value
            if (description.toLowerCase().includes('age')) {
              const age = parseInt(value);
              if (!isNaN(age)) profileData.age = age;
            } else if (description.toLowerCase().includes('state')) {
              profileData.state = value;
            } else if (description.toLowerCase().includes('marital')) {
              profileData.marital_status = value;
            } else if (description.toLowerCase().includes('employment')) {
              profileData.employment_status = value;
            } else if (description.toLowerCase().includes('occupation')) {
              profileData.occupation = value;
            } else if (description.toLowerCase().includes('risk')) {
              profileData.risk_tolerance = value;
            } else if (description.toLowerCase().includes('gender')) {
              profileData.gender = value;
            } else if (description.toLowerCase().includes('name')) {
              // Names should be handled by the User model, not profile
              // For now, store in notes until we add name handling to profile endpoint
              profileData = { 
                notes: `${description}: ${value}` 
              };
            } else {
              // Generic field - store in a combined note
              profileData = { 
                notes: `${description}: ${value}` 
              };
            }
            break;
            
          case 'Contact & Location':
            if (description.toLowerCase().includes('phone')) {
              profileData.phone = value;
            } else if (description.toLowerCase().includes('address')) {
              profileData.address = value;
            } else if (description.toLowerCase().includes('city')) {
              profileData.city = value;
            } else if (description.toLowerCase().includes('zip')) {
              profileData.zip_code = value;
            } else if (description.toLowerCase().includes('emergency')) {
              profileData.emergency_contact = value;
            }
            break;
            
          default:
            profileData = {
              notes: `${description}: ${value}`
            };
        }
        
        return profileApi.createOrUpdateProfile(profileData);
        
      case 'benefits':
        return profileApi.addBenefit({
          benefit_type: subcategory || 'other',
          benefit_name: description,
          estimated_monthly_benefit: parseFloat(notes) || undefined,
          notes: notes
        });
        
      case 'tax_info':
        let taxData: any = {
          tax_year: new Date().getFullYear(),
          notes: `${description}: ${notes}`
        };
        
        // Try to parse numeric values for specific tax fields
        const numericValue = parseFloat(notes);
        if (!isNaN(numericValue)) {
          if (description.toLowerCase().includes('bracket')) {
            taxData.federal_tax_bracket = numericValue;
          } else if (description.toLowerCase().includes('rate')) {
            taxData.effective_tax_rate = numericValue;
          } else if (description.toLowerCase().includes('income')) {
            taxData.adjusted_gross_income = numericValue;
          }
        }
        
        return profileApi.addTaxInfo(taxData);
        
      default:
        throw new Error(`Unsupported category: ${category}`);
    }
  }
};