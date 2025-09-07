/**
 * QuickFix Component - Replaces static assumptions with interactive ones
 */
import React, { useEffect, useState } from 'react';

export const EnableAssumptionsEditing: React.FC = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    
    const replaceStaticAssumptions = () => {
      // Look for the static assumptions section by finding text content
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );

      let foundAssumptions = false;
      let node;
      
      while (node = walker.nextNode()) {
        if (node.textContent?.includes('Key Assumptions Used')) {
          const parentSection = node.parentElement?.closest('div, section');
          if (parentSection && !parentSection.querySelector('#interactive-assumptions')) {
            replaceWithInteractive(parentSection);
            foundAssumptions = true;
            break;
          }
        }
      }
      
      return foundAssumptions;
    };

    const replaceWithInteractive = (section: Element) => {
      // Create interactive assumptions container
      const container = document.createElement('div');
      container.id = 'interactive-assumptions';
      container.className = 'bg-gray-800 rounded-xl p-6 border border-gray-700';
      
      container.innerHTML = `
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-xl font-semibold text-white flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            </svg>
            Key Assumptions Used
          </h3>
          <div class="flex items-center gap-3">
            <button id="reset-defaults" class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-gray-300 rounded text-sm transition-colors">
              Reset Defaults
            </button>
            <button id="apply-changes" class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-all transform hover:scale-105 shadow-lg shadow-blue-500/20" style="display: none;">
              Apply Changes & Recalculate
            </button>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          ${createAssumptionCard('salary_growth', 'Salary Growth', '💰', 2.0, 0, 10, 0.5, 'Industry average for your role and experience')}
          ${createAssumptionCard('real_estate', 'Real Estate', '🏠', 2.5, 0, 8, 0.5, 'Based on your property locations and market data')}
          ${createAssumptionCard('stock_returns', 'Stock Returns', '📈', 5.0, 0, 15, 0.5, 'Historical S&P 500 average: 10%, we use conservative 8%')}
          ${createAssumptionCard('retirement_401k', '401k Return', '🏦', 6.5, 0, 12, 0.5, 'Conservative retirement account growth rate')}
          ${createAssumptionCard('inflation', 'Inflation', '📊', 2.5, 0, 6, 0.5, 'Federal Reserve target + 0.5% buffer')}
        </div>

        <div id="warning-message" class="hidden flex items-start gap-3 p-4 bg-orange-900/30 border border-orange-600 rounded-lg">
          <svg class="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.316 15.5c-.77.833.192 2.5 1.732 2.5z"></path>
          </svg>
          <div>
            <p class="text-sm text-orange-300 font-medium mb-1">Projection Parameters Modified</p>
            <p class="text-sm text-orange-300/80">
              Adjusting these assumptions will recalculate all projections and confidence intervals. 
              Click "Apply Changes" to see updated results with your custom parameters.
            </p>
          </div>
        </div>
      `;

      // Replace the original section
      section.parentNode?.replaceChild(container, section);
      
      // Add interactivity
      addInteractivity(container);
    };

    const createAssumptionCard = (key: string, label: string, icon: string, defaultValue: number, min: number, max: number, step: number, description: string) => {
      return `
        <div class="assumption-card bg-gray-700 rounded-lg p-4 transition-all duration-200" data-key="${key}" data-default="${defaultValue}">
          <div class="flex items-center gap-2 mb-3">
            <span>${icon}</span>
            <span class="text-sm text-gray-300 font-medium">${label}</span>
          </div>
          
          <div class="value-display text-2xl font-bold text-green-400 mb-4">
            ${defaultValue.toFixed(1)}%
          </div>
          
          <div class="mb-3">
            <input 
              type="range" 
              min="${min}" 
              max="${max}" 
              step="${step}" 
              value="${defaultValue}"
              class="assumption-slider w-full h-2 rounded-lg appearance-none cursor-pointer"
              data-key="${key}"
            />
          </div>
          
          <div class="flex justify-between text-xs text-gray-500 mb-2">
            <span>${min}%</span>
            <span>${max}%</span>
          </div>
          
          <div class="text-xs text-gray-400 leading-tight">
            ${description}
          </div>
          
          <div class="default-indicator text-xs text-blue-400 mt-2 font-medium" style="display: none;">
            Default: ${defaultValue}%
          </div>
        </div>
      `;
    };

    const addInteractivity = (container: Element) => {
      const assumptions = {
        salary_growth: 2.0,
        real_estate: 2.5,
        stock_returns: 5.0,
        retirement_401k: 6.5,
        inflation: 2.5
      };
      
      let hasChanges = false;
      
      const updateUI = () => {
        const applyBtn = container.querySelector('#apply-changes') as HTMLElement;
        const warningMsg = container.querySelector('#warning-message') as HTMLElement;
        
        if (hasChanges) {
          applyBtn.style.display = 'block';
          warningMsg.classList.remove('hidden');
        } else {
          applyBtn.style.display = 'none';
          warningMsg.classList.add('hidden');
        }
      };

      // Add slider event listeners
      container.querySelectorAll('.assumption-slider').forEach(slider => {
        const input = slider as HTMLInputElement;
        const key = input.dataset.key!;
        const card = input.closest('.assumption-card')!;
        const valueDisplay = card.querySelector('.value-display')!;
        const defaultIndicator = card.querySelector('.default-indicator') as HTMLElement;
        const defaultValue = parseFloat(card.dataset.default!);

        input.addEventListener('input', (e) => {
          const value = parseFloat((e.target as HTMLInputElement).value);
          assumptions[key as keyof typeof assumptions] = value;
          valueDisplay.textContent = `${value.toFixed(1)}%`;
          
          const isChanged = Math.abs(value - defaultValue) > 0.001;
          
          if (isChanged) {
            card.classList.add('ring-2', 'ring-blue-500', 'bg-gray-700/80');
            defaultIndicator.style.display = 'block';
            valueDisplay.classList.remove('text-green-400');
            valueDisplay.classList.add('text-blue-400');
          } else {
            card.classList.remove('ring-2', 'ring-blue-500', 'bg-gray-700/80');
            defaultIndicator.style.display = 'none';
            valueDisplay.classList.remove('text-blue-400');
            valueDisplay.classList.add('text-green-400');
          }
          
          hasChanges = Object.keys(assumptions).some(k => 
            Math.abs(assumptions[k as keyof typeof assumptions] - parseFloat(container.querySelector(`[data-key="${k}"]`)!.dataset.default!)) > 0.001
          );
          
          updateUI();
        });
      });

      // Reset button
      container.querySelector('#reset-defaults')?.addEventListener('click', () => {
        container.querySelectorAll('.assumption-card').forEach(card => {
          const key = (card as HTMLElement).dataset.key!;
          const defaultValue = parseFloat((card as HTMLElement).dataset.default!);
          const slider = card.querySelector('.assumption-slider') as HTMLInputElement;
          const valueDisplay = card.querySelector('.value-display')!;
          const defaultIndicator = card.querySelector('.default-indicator') as HTMLElement;
          
          slider.value = defaultValue.toString();
          valueDisplay.textContent = `${defaultValue.toFixed(1)}%`;
          assumptions[key as keyof typeof assumptions] = defaultValue;
          
          card.classList.remove('ring-2', 'ring-blue-500', 'bg-gray-700/80');
          defaultIndicator.style.display = 'none';
          valueDisplay.classList.remove('text-blue-400');
          valueDisplay.classList.add('text-green-400');
        });
        
        hasChanges = false;
        updateUI();
      });

      // Apply changes button
      container.querySelector('#apply-changes')?.addEventListener('click', async () => {
        const btn = container.querySelector('#apply-changes') as HTMLButtonElement;
        btn.textContent = 'Applying...';
        btn.disabled = true;
        
        try {
          // Here you would normally call your API
          console.log('Applying new assumptions:', assumptions);
          
          // Simulate API call
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          // Show success
          btn.textContent = 'Applied Successfully!';
          btn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
          btn.classList.add('bg-green-600');
          
          setTimeout(() => {
            btn.textContent = 'Apply Changes & Recalculate';
            btn.classList.remove('bg-green-600');
            btn.classList.add('bg-blue-600', 'hover:bg-blue-700');
            btn.disabled = false;
            hasChanges = false;
            updateUI();
          }, 3000);
          
        } catch (error) {
          console.error('Failed to apply changes:', error);
          btn.textContent = 'Failed - Try Again';
          btn.classList.add('bg-red-600');
          btn.disabled = false;
          
          setTimeout(() => {
            btn.textContent = 'Apply Changes & Recalculate';
            btn.classList.remove('bg-red-600');
            btn.classList.add('bg-blue-600');
          }, 3000);
        }
      });
    };

    // Try to replace immediately
    if (!replaceStaticAssumptions()) {
      // If not found, try periodically
      const interval = setInterval(() => {
        if (replaceStaticAssumptions()) {
          clearInterval(interval);
        }
      }, 1000);

      // Clear interval after 30 seconds to avoid infinite polling
      setTimeout(() => clearInterval(interval), 30000);
    }

  }, []);

  return null; // This component doesn't render anything directly
};

export default EnableAssumptionsEditing;