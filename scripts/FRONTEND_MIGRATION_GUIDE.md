# WealthPath AI - Frontend Data Migration Guide

Since your frontend can successfully connect to Supabase, the easiest approach is to use the existing forms to recreate the user data.

## 📊 **Local Data Summary (Ready for Entry)**

### **Users to Recreate** (8 total)

#### 1. **Primary Admin User**
- **Email**: `debashishroy@gmail.com`  
- **Name**: Debashish Roy
- **Status**: Active, Email Verified
- **Created**: Aug 10, 2025

#### 2. **Test User (Gmail)**
- **Email**: `test@gmail.com`
- **Name**: test test  
- **Status**: Active, Email Verified
- **Created**: Aug 21, 2025

#### 3. **Test User (Example.com)**
- **Email**: `test@example.com`
- **Name**: Test User
- **Status**: Active, Email Verified  
- **Created**: Aug 26, 2025

#### 4. **Test User 1 (Gmail)**
- **Email**: `test1@gmail.com`
- **Name**: test1 test1
- **Status**: Active, Email Verified
- **Created**: Aug 24, 2025

#### 5. **Test User (Gmail)**
- **Email**: `testuser@gmail.com`
- **Name**: Test User
- **Status**: Active, Email Verified
- **Created**: Aug 29, 2025

#### 6. **Test User 1 (Example)**
- **Email**: `test1@example.com`
- **Name**: Test User1
- **Status**: Active, Email Verified
- **Created**: Aug 29, 2025

#### 7. **Latest Test User**
- **Email**: `testuser@example.com`
- **Name**: Test User
- **Status**: Active, Email Verified
- **Created**: Sep 6, 2025

#### 8. **Disabled Test User**
- **Email**: `test@example.com_disabled`
- **Status**: Not verified/disabled
- **Created**: Aug 14, 2025

---

## 👤 **User Profile Data**

### **Debashish Roy (Primary User)**
- **Age**: 54
- **Risk Tolerance**: Moderate
- **Employment**: Employed
- **Marital Status**: Married
- **State**: NC
- **Occupation**: IT Consultant
- **Risk Score**: 6
- **Retirement Age**: 67
- **Notes**: "Name: DR"

### **test@gmail.com User**
- **Age**: 40
- **Risk Tolerance**: Aggressive  
- **Employment**: Employed
- **Marital Status**: Married
- **State**: NJ, USA
- **Occupation**: Software Engineer
- **Risk Score**: 6
- **Retirement Age**: 67

### **Other Test Users**
- Basic profiles with minimal data
- Most have Risk Score: 6, Retirement Age: 67

---

## 💰 **Benefits Data (4 records)**

### **Debashish Roy Benefits**

#### **Social Security**
- **Benefit Name**: Primary Social Security
- **Monthly Amount**: $4,005.00
- **Claiming Age**: 67
- **Estimated Amount**: $4,000

#### **401(k) Plan**  
- **Current Balance**: $250,000.00
- **Annual Contribution**: $30,500.00
- **Employer Match**: "100% up to 3%"
- **Vesting**: "25% per year starting year 1"

### **test@gmail.com Benefits**

#### **Social Security**
- **Monthly Amount**: $2,000.00

#### **401(k) Plan**
- **Current Balance**: $125,000.00  
- **Annual Contribution**: $23,000.00
- **Employer Match**: "100% up to 3%"
- **Vesting**: "immediate"

---

## 💼 **Investment Preferences (1 record)**

### **Debashish Roy Investment Settings**
- **Risk Tolerance Score**: 7 (out of 10)
- **Investment Timeline**: 15 years
- **Rebalancing**: Annual
- **Philosophy**: Balanced
- **ESG Level**: 1
- **International Allocation**: 10.00%
- **Alternative Investment Interest**: 50% (previously true)
- **Individual Stock Tolerance**: 0% (previously false)  
- **Tax Loss Harvesting**: Enabled
- **Dollar Cost Averaging**: Enabled

---

## 🏛️ **Estate Planning (4 documents for Debashish Roy)**

### **Document 1: Beneficiary Designation**
- **Name**: "Beneficiary Designation DR"
- **Status**: Current
- **Last Updated**: Aug 28, 2025
- **Attorney**: "Smith & Associate Law firm"

### **Document 2: Healthcare Directive**
- **Name**: "DR Healthcare Directive"  
- **Status**: Current
- **Last Updated**: Aug 28, 2025
- **Attorney**: "Smith"

### **Document 3: Will**
- **Name**: "DR Will"
- **Status**: Current  
- **Last Updated**: Aug 28, 2025
- **Next Review**: Aug 28, 2026

### **Document 4: Power of Attorney**
- **Name**: "DR POA"
- **Status**: Current
- **Last Updated**: Aug 28, 2025
- **Next Review**: Aug 28, 2027

---

## 🛡️ **Insurance Policies (2 policies for Debashish Roy)**

### **Auto Insurance**
- **Policy Name**: "Auto Insurance"
- **Coverage**: $50,000.00
- **Annual Premium**: $1,400.00
- **Primary Beneficiary**: "AR"

### **Homeowners Insurance**  
- **Policy Name**: "Home Insurance"
- **Coverage**: $800,000.00
- **Annual Premium**: $1,300.00
- **Primary Beneficiary**: "AR"

---

## 🚀 **Frontend Data Entry Steps**

### **Step 1: Create Users**
1. **Register each user** through your frontend registration process
2. **Use the emails and names** listed above
3. **Set temporary passwords** (users can reset later)
4. **Verify email addresses** if needed

### **Step 2: Complete User Profiles**
1. **Login as each user** 
2. **Navigate to Profile/Settings**
3. **Fill in the demographic data** (age, occupation, etc.)
4. **Set risk tolerance scores**

### **Step 3: Enter Benefits Data**
1. **Go to Benefits Management**
2. **Add Social Security benefits** with amounts and ages
3. **Add 401(k) plans** with balances and contribution details
4. **Set employer match formulas**

### **Step 4: Set Investment Preferences**
1. **Navigate to Investment Preferences**
2. **Set risk tolerance score** (7 for Debashish)
3. **Configure timeline** (15 years)
4. **Set asset allocation preferences**
5. **Enable/disable features** as listed

### **Step 5: Add Estate Planning Documents**
1. **Go to Estate Planning section**
2. **Add each document** with names and statuses
3. **Set attorney contacts** and review dates
4. **Mark documents as current**

### **Step 6: Enter Insurance Policies**
1. **Navigate to Insurance Management**
2. **Add Auto and Home policies**
3. **Set coverage amounts and premiums**
4. **Add beneficiary information**

---

## ✅ **Migration Verification**

After entering data through the frontend:

1. **Test all major features** with the migrated data
2. **Verify calculations** work correctly
3. **Check that relationships** between data are maintained
4. **Ensure chat/advisory features** can access the data properly

This approach leverages your existing, working frontend forms and ensures all data validation and relationships are properly handled by your application logic.

**Estimate: 30-45 minutes** to recreate the essential data for the primary user (Debashish Roy) with all associated profiles, benefits, investments, estate planning, and insurance data.