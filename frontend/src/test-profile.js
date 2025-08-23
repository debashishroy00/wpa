/**
 * Test script for profile API functionality
 * Run this with: node test-profile.js
 */

// Test data for profile entry
const testProfileEntry = {
  category: "profile",
  subcategory: "personal_info", 
  description: "Age",
  amount: 0,
  currency: "USD",
  frequency: "one_time",
  notes: "35"
};

const testBenefitEntry = {
  category: "benefits",
  subcategory: "social_security",
  description: "Monthly Social Security",
  amount: 0,
  currency: "USD", 
  frequency: "one_time",
  notes: "2800"
};

const testTaxEntry = {
  category: "tax_info",
  subcategory: "filing_status", 
  description: "Tax Bracket",
  amount: 0,
  currency: "USD",
  frequency: "one_time", 
  notes: "24"
};

console.log("Profile Entry Test Data:");
console.log(JSON.stringify(testProfileEntry, null, 2));

console.log("\nBenefit Entry Test Data:");
console.log(JSON.stringify(testBenefitEntry, null, 2));

console.log("\nTax Entry Test Data:");
console.log(JSON.stringify(testTaxEntry, null, 2));

console.log("\n✅ Test data generated successfully");
console.log("💡 Use these in the frontend form to test profile entries");