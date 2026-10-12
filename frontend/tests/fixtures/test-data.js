/**
 * Test Data Fixtures for Playwright E2E Tests
 */

export function generateTestCitizen() {
  const timestamp = Date.now()
  return {
    fullName: `Test Citizen ${timestamp}`,
    email: `citizen_${timestamp}@testdomain.org`,
    password: `P@ssw0rd_${timestamp}`,
    age: '24',
    gender: 'FEMALE',
    stateId: '23', // Tamil Nadu
    annualIncome: '180000',
    occupation: 'Student',
    education: 'Higher Secondary (12th)',
    category: 'General',
    disabilityStatus: false,
  }
}

export function getConfirmedTestCitizen() {
  return {
    fullName: 'E2E Test Citizen',
    email: 'test_citizen_e2e@schemesetu.test',
    password: process.env.TEST_CITIZEN_PASSWORD || 'E2E_Test_Password_2026!',
    age: '24',
    gender: 'FEMALE',
    stateId: '23', // Tamil Nadu
    annualIncome: '180000',
    occupation: 'Student',
    education: 'Higher Secondary (12th)',
    category: 'General',
    disabilityStatus: false,
  }
}

export function getConfirmedUserB() {
  return {
    fullName: 'E2E Citizen User B',
    email: 'test_citizen_user_b@schemesetu.test',
    password: process.env.TEST_CITIZEN_PASSWORD || 'E2E_Test_Password_2026!',
    age: '30',
    gender: 'MALE',
    stateId: '23',
    annualIncome: '250000',
    occupation: 'Farmer',
    education: "Graduate / Bachelor's",
    category: 'OBC',
    disabilityStatus: false,
  }
}
