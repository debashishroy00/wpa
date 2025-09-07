/**
 * WealthPath AI - Profile Data React Query Hooks
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { profileApi } from '../utils/profile-api';

// Query Keys
export const profileQueryKeys = {
  all: ['profile'] as const,
  profile: () => [...profileQueryKeys.all, 'user-profile'] as const,
  family: () => [...profileQueryKeys.all, 'family'] as const,
  benefits: () => [...profileQueryKeys.all, 'benefits'] as const,
  taxInfo: (year?: number) => [...profileQueryKeys.all, 'tax-info', year] as const,
  complete: () => [...profileQueryKeys.all, 'complete'] as const,
};

// User Profile Queries
export const useProfileQuery = () => {
  return useQuery({
    queryKey: profileQueryKeys.profile(),
    queryFn: () => {
      console.log('👤 Calling profileApi.getProfile');
      return profileApi.getProfile();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useCompleteProfileQuery = () => {
  return useQuery({
    queryKey: profileQueryKeys.complete(),
    queryFn: () => {
      console.log('🔄 Calling profileApi.getCompleteProfile');
      return profileApi.getCompleteProfile();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Family Queries
export const useFamilyMembersQuery = () => {
  return useQuery({
    queryKey: profileQueryKeys.family(),
    queryFn: profileApi.getFamilyMembers,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Benefits Queries
export const useBenefitsQuery = () => {
  return useQuery({
    queryKey: profileQueryKeys.benefits(),
    queryFn: profileApi.getBenefits,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Tax Info Queries
export const useTaxInfoQuery = (taxYear?: number) => {
  return useQuery({
    queryKey: profileQueryKeys.taxInfo(taxYear),
    queryFn: () => profileApi.getTaxInfo(taxYear),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Profile Mutations
export const useCreateOrUpdateProfileMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => profileApi.createOrUpdateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.profile() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

export const useUpdateProfileMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => profileApi.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.profile() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

// Family Mutations
export const useAddFamilyMemberMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => profileApi.addFamilyMember(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.family() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

export const useUpdateFamilyMemberMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => profileApi.updateFamilyMember(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.family() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

export const useDeleteFamilyMemberMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => profileApi.deleteFamilyMember(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.family() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

// Benefits Mutations
export const useAddBenefitMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => profileApi.addBenefit(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.benefits() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

export const useUpdateBenefitMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => profileApi.updateBenefit(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.benefits() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

export const useDeleteBenefitMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => profileApi.deleteBenefit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.benefits() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

// Tax Info Mutations
export const useAddTaxInfoMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => profileApi.addTaxInfo(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.taxInfo() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

export const useUpdateTaxInfoMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => profileApi.updateTaxInfo(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.taxInfo() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

export const useDeleteTaxInfoMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => profileApi.deleteTaxInfo(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.taxInfo() });
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.complete() });
    },
  });
};

// Generic Profile Entry Creation (for the form)
export const useCreateProfileEntryMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => profileApi.createEntry(data),
    onSuccess: () => {
      // Invalidate all profile-related queries
      queryClient.invalidateQueries({ queryKey: profileQueryKeys.all });
    },
  });
};