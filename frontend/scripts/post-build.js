import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('🔄 Running post-build script...');

const distDir = path.join(__dirname, '../dist');
const landingFile = path.join(__dirname, '../landing.html');

try {
  // Read the current built index.html (React app)
  const reactAppHtml = fs.readFileSync(path.join(distDir, 'index.html'), 'utf8');
  
  // Read the landing page
  const landingHtml = fs.readFileSync(landingFile, 'utf8');
  
  // Save React app as app.html
  fs.writeFileSync(path.join(distDir, 'app.html'), reactAppHtml);
  console.log('✅ Saved React app as dist/app.html');
  
  // Replace index.html with landing page
  fs.writeFileSync(path.join(distDir, 'index.html'), landingHtml);
  console.log('✅ Replaced dist/index.html with landing page');
  
  console.log('🎉 Post-build complete! Landing page at root, React app at /app.html');
  
} catch (error) {
  console.error('❌ Post-build script failed:', error);
  process.exit(1);
}