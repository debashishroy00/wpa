const fs = require('fs');
const path = require('path');
const glob = require('glob');

const MAX_LINES = 300;
const HARD_LIMIT = 500;

// Get the project root directory (where this script's parent is)
const projectRoot = path.dirname(__dirname);

let hasErrors = false;
let hasWarnings = false;

console.log('🔍 Checking file sizes...\n');
console.log(`Project root: ${projectRoot}\n`);

// Check frontend files
console.log('Checking frontend files...');
const frontendPattern = path.join(projectRoot, 'frontend', 'src', '**', '*.{ts,tsx,js,jsx}').replace(/\\/g, '/');
const frontendFiles = glob.sync(frontendPattern);
console.log(`Frontend pattern: ${frontendPattern}`);
console.log(`Found ${frontendFiles.length} frontend files`);

frontendFiles.forEach(file => {
  const content = fs.readFileSync(file, 'utf8');
  const lines = content.split('\n').length;
  
  if (lines > HARD_LIMIT) {
    console.error(`❌ ERROR: ${path.relative(projectRoot, file)}`);
    console.error(`   ${lines} lines (max allowed: ${HARD_LIMIT})\n`);
    hasErrors = true;
  } else if (lines > MAX_LINES) {
    console.warn(`⚠️  WARNING: ${path.relative(projectRoot, file)}`);
    console.warn(`   ${lines} lines (target: ${MAX_LINES})\n`);
    hasWarnings = true;
  }
});

// Check backend files
console.log('Checking backend files...');
const backendPattern = path.join(projectRoot, 'backend', 'app', '**', '*.py').replace(/\\/g, '/');
const backendFiles = glob.sync(backendPattern);
console.log(`Backend pattern: ${backendPattern}`);
console.log(`Found ${backendFiles.length} backend files`);

backendFiles.forEach(file => {
  const content = fs.readFileSync(file, 'utf8');
  const lines = content.split('\n').length;
  
  if (lines > HARD_LIMIT) {
    console.error(`❌ ERROR: ${path.relative(projectRoot, file)}`);
    console.error(`   ${lines} lines (max allowed: ${HARD_LIMIT})\n`);
    hasErrors = true;
  } else if (lines > MAX_LINES) {
    console.warn(`⚠️  WARNING: ${path.relative(projectRoot, file)}`);
    console.warn(`   ${lines} lines (target: ${MAX_LINES})\n`);
    hasWarnings = true;
  }
});

if (hasErrors) {
  console.error('\n❌ Quality check FAILED. Fix files over 500 lines before proceeding.');
  process.exit(1);
} else if (hasWarnings) {
  console.warn('\n⚠️  Quality check passed with warnings. Consider refactoring large files.');
} else {
  console.log('\n✅ All files within size limits!');
}

// Show top 10 largest files
console.log('\n📊 Top 10 Largest Files:');
const allFiles = [...frontendFiles, ...backendFiles];

const fileSizes = allFiles.map(file => {
  const content = fs.readFileSync(file, 'utf8');
  return { file: path.relative(projectRoot, file), lines: content.split('\n').length };
}).sort((a, b) => b.lines - a.lines).slice(0, 10);

fileSizes.forEach((item, index) => {
  const emoji = item.lines > HARD_LIMIT ? '❌' : item.lines > MAX_LINES ? '⚠️' : '✅';
  console.log(`${emoji} ${index + 1}. ${item.file}: ${item.lines} lines`);
});

console.log('\n💡 Quality Guidelines:');
console.log('• New files should be < 300 lines');
console.log('• Service files: < 200 lines');
console.log('• Component files: < 150 lines');
console.log('• Router files: < 100 lines');
console.log('• Functions: < 30 lines each');