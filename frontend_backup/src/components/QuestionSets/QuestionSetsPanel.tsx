import React from 'react';
import { QUESTION_SETS, QuestionCategory } from '../../content/question_sets';

type Props = {
  onSelect: (prompt: string) => void;
};

const Panel: React.FC<Props> = ({ onSelect }) => {
  return (
    <div style={{
      border: '1px solid #2d2d4e',
      borderRadius: 12,
      padding: 12,
      background: '#111827',
      color: '#e5e7eb',
      marginBottom: 12
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div style={{ fontWeight: 700 }}>Common Questions</div>
        <div style={{ fontSize: 12, opacity: 0.7 }}>Tap to run — chat for follow‑ups</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
        {QUESTION_SETS.map((cat: QuestionCategory) => (
          <div key={cat.id} style={{ border: '1px solid #374151', borderRadius: 10, padding: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6, color: '#93c5fd' }}>{cat.title}</div>
            <div style={{ display: 'grid', gap: 6 }}>
              {cat.tiles.map(tile => (
                <button
                  key={tile.id}
                  onClick={() => onSelect(tile.prompt)}
                  style={{
                    textAlign: 'left',
                    border: '1px solid #374151',
                    background: '#0b1220',
                    color: '#e5e7eb',
                    borderRadius: 8,
                    padding: '8px 10px',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{tile.label}</div>
                  {tile.sublabel && <div style={{ fontSize: 12, opacity: 0.75 }}>{tile.sublabel}</div>}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Panel;

