import React, { Suspense } from 'react';

// Lazy-loaded ProfileManagementPage component
const ProfileManagementPage = React.lazy(() => import('../components/profile/ProfileManagementPage'));

interface ProfileProps {
  onNext: () => void;
}

const Profile: React.FC<ProfileProps> = ({ onNext }) => {
  return (
    <div style={{ 
      background: '#ffffff',
      borderRadius: '12px',
      margin: '-40px',
      minHeight: '500px'
    }}>
      {/* Step Header */}
      <div style={{
        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        color: '#e2e8f0',
        padding: '20px 30px',
        borderRadius: '12px 12px 0 0',
        marginBottom: '0'
      }}>
        <h2 style={{ fontSize: '1.8em', margin: '0 0 10px 0', fontWeight: 'bold' }}>
          👤 Profile & Family Information
        </h2>
        <p style={{ margin: '0', opacity: '0.9', fontSize: '1.1em' }}>
          Start by setting up your personal profile, family members, benefits, and tax information
        </p>
      </div>
      
      {/* Profile Management Page */}
      <Suspense fallback={<div>Loading...</div>}>
        <ProfileManagementPage />
      </Suspense>
      
      {/* Continue Button */}
      <div style={{
        padding: '20px 30px',
        borderTop: '1px solid #e2e8f0',
        background: '#f8fafc',
        borderRadius: '0 0 12px 12px'
      }}>
        <button
          onClick={onNext}
          style={{
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            color: '#e2e8f0',
            border: 'none',
            padding: '12px 30px',
            borderRadius: '8px',
            fontSize: '1.1em',
            fontWeight: 'bold',
            cursor: 'pointer',
            float: 'right'
          }}
        >
          Continue to Financial Data →
        </button>
        <div style={{ clear: 'both' }}></div>
      </div>
    </div>
  );
};

export default Profile;