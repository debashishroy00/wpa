/**
 * Calculation Display Component
 * Enhanced display for financial calculations with step-by-step breakdown
 */
import React from 'react';
import '../../styles/calculation-display.css';

interface CalculationStep {
  step: number;
  description: string;
  formula: string;
  result: string;
}

interface CalculationDisplayProps {
  content: string;
}

const CalculationDisplay: React.FC<CalculationDisplayProps> = ({ content }) => {
  const parseCalculations = (content: string): CalculationStep[] => {
    const steps: CalculationStep[] = [];
    
    // Match patterns like "**Step 1:** Description = Result"
    const stepPattern = /\*\*Step (\d+):\*\*\s*(.*?)\s*=\s*([^\n]*)/g;
    let match;
    
    while ((match = stepPattern.exec(content)) !== null) {
      steps.push({
        step: parseInt(match[1]),
        description: match[2].trim(),
        formula: match[2].trim(),
        result: match[3].trim()
      });
    }
    
    return steps;
  };
  
  const extractResult = (content: string): string | null => {
    const resultPattern = /\*\*Result:\*\*\s*(.*?)(?:\n|$)/;
    const match = content.match(resultPattern);
    return match ? match[1].trim() : null;
  };
  
  const highlightCalculations = (text: string): string => {
    // Highlight currency amounts
    text = text.replace(/\$[\d,]+\.?\d*/g, '<span class="currency">$&</span>');
    
    // Highlight percentages
    text = text.replace(/\d+\.?\d*%/g, '<span class="percentage">$&</span>');
    
    // Highlight mathematical operators
    text = text.replace(/([×\*\+\-\÷/=])/g, '<span class="operator">$1</span>');
    
    return text;
  };
  
  const hasCalculations = content.includes('**Step') && content.includes('=');
  
  if (!hasCalculations) {
    // Regular message - just highlight any numbers/percentages
    return (
      <div 
        className="message-content"
        dangerouslySetInnerHTML={{ __html: highlightCalculations(content) }}
      />
    );
  }
  
  const steps = parseCalculations(content);
  const finalResult = extractResult(content);
  
  return (
    <div className="calculation-display">
      {steps.length > 0 && (
        <div className="calculation-steps">
          <div className="calculation-header">
            <span className="calc-icon">🧮</span>
            <span className="calc-title">Financial Calculation</span>
          </div>
          
          {steps.map((step, index) => (
            <div key={index} className="calculation-step">
              <div className="step-number">
                Step {step.step}
              </div>
              <div className="step-content">
                <div 
                  className="step-formula"
                  dangerouslySetInnerHTML={{ 
                    __html: highlightCalculations(step.formula) 
                  }}
                />
                <div className="step-equals">=</div>
                <div 
                  className="step-result"
                  dangerouslySetInnerHTML={{ 
                    __html: highlightCalculations(step.result) 
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
      
      {finalResult && (
        <div className="calculation-result">
          <div className="result-header">
            <span className="result-icon">💡</span>
            <span className="result-title">Result</span>
          </div>
          <div 
            className="result-content"
            dangerouslySetInnerHTML={{ 
              __html: highlightCalculations(finalResult) 
            }}
          />
        </div>
      )}
      
      {/* Show any remaining content that's not part of the calculation */}
      {(() => {
        let remainingContent = content;
        
        // Remove step patterns
        remainingContent = remainingContent.replace(/\*\*Step \d+:\*\*.*?=.*?(?=\n|$)/g, '');
        
        // Remove result pattern
        remainingContent = remainingContent.replace(/\*\*Result:\*\*.*?(?=\n|$)/g, '');
        
        // Clean up extra whitespace
        remainingContent = remainingContent.replace(/\n\s*\n/g, '\n').trim();
        
        if (remainingContent) {
          return (
            <div className="calculation-explanation">
              <div 
                dangerouslySetInnerHTML={{ 
                  __html: highlightCalculations(remainingContent) 
                }}
              />
            </div>
          );
        }
        return null;
      })()}
    </div>
  );
};

export default CalculationDisplay;