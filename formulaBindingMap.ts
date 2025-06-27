/**
 * Real Estate Investment Analyzer - Formula Binding Map
 * Complete mapping of input fields to state variables and consuming formulas
 * Last Updated: 2025-06-27
 */

interface InputBinding {
  page: string;
  section: string;
  inputField: string;
  domId: string;
  centralStateKey: string;
  consumingFormulas: string[];
  updateFunctions: string[];
  inputType: 'number' | 'text' | 'select' | 'slider' | 'calculated';
  formatType?: 'currency' | 'percentage' | 'integer' | 'decimal';
}

interface CalculationDependency {
  formula: string;
  dependencies: string[];
  updateTriggers: string[];
}

export const FORMULA_BINDING_MAP = {
  
  // ========================================
  // GLOBAL INPUTS (Property Header)
  // ========================================
  globalInputs: [
    {
      page: "Global",
      section: "Property Header",
      inputField: "Bedrooms",
      domId: "bedrooms",
      centralStateKey: "deal.bedrooms",
      consumingFormulas: ["propertyDescription", "comparableSales", "rentEstimate"],
      updateFunctions: ["updateAllTabCalculations()"],
      inputType: "number" as const,
      formatType: "integer" as const
    },
    {
      page: "Global", 
      section: "Property Header",
      inputField: "Bathrooms",
      domId: "bathrooms",
      centralStateKey: "deal.bathrooms",
      consumingFormulas: ["propertyDescription", "comparableSales", "rentEstimate"],
      updateFunctions: ["updateAllTabCalculations()"],
      inputType: "number" as const,
      formatType: "integer" as const
    },
    {
      page: "Global",
      section: "Property Header", 
      inputField: "Square Feet",
      domId: "square-feet",
      centralStateKey: "deal.squareFeet",
      consumingFormulas: ["propertyDescription", "comparableSales", "rentEstimate"],
      updateFunctions: ["updateAllTabCalculations()"],
      inputType: "number" as const,
      formatType: "integer" as const
    },
    {
      page: "Global",
      section: "Property Header",
      inputField: "ARV (After Repair Value)",
      domId: "arv",
      centralStateKey: "deal.arv",
      consumingFormulas: [
        "wholesaleMAO", "installmentMAO", "subjectToOffers", "sellerFinancePrice",
        "ackermanOffers", "compareAll", "allDispositionStrategies", "wrapPriceToBuyer",
        "leaseOptionBaseCashToClose", "maxProfitFlipperPrice", "brrrInvestorPrice"
      ],
      updateFunctions: [
        "updateAllTabCalculations()", "recalculateWholesale()", "recalculateInstallment()",
        "recalculateSubjectTo()", "recalculateSellerFinance()", "recalculateDispositions()",
        "updateWrapConfiguration()", "updateLeaseOptionCalculation()"
      ],
      inputType: "number" as const,
      formatType: "currency" as const
    },
    {
      page: "Global",
      section: "Property Header",
      inputField: "Repairs",
      domId: "repairs", 
      centralStateKey: "deal.repairs",
      consumingFormulas: [
        "wholesaleMAO", "installmentMAO", "subjectToOffers", "sellerFinancePrice",
        "ackermanOffers", "compareAll", "allDispositionStrategies", "volumeFlipperPrice",
        "brrrInvestorPrice", "maxProfitFlipperPrice", "calculateCashOffer"
      ],
      updateFunctions: [
        "updateAllTabCalculations()", "recalculateWholesale()", "recalculateInstallment()",
        "recalculateSubjectTo()", "recalculateSellerFinance()", "recalculateDispositions()",
        "updateWholesaleBuyerMatrix()", "calculateCashOffer()"
      ],
      inputType: "number" as const,
      formatType: "currency" as const
    },
    {
      page: "Global",
      section: "Property Header",
      inputField: "Monthly Rent",
      domId: "rent",
      centralStateKey: "deal.rent",
      consumingFormulas: [
        "subjectToCashFlow", "sellerFinanceCashFlow", "rentRuleInvestorPrice",
        "cashFlowAnalysis", "compareAll", "calculateCashOffer"
      ],
      updateFunctions: [
        "updateAllTabCalculations()", "recalculateSubjectTo()", "recalculateSellerFinance()",
        "recalculateDispositions()", "updateWholesaleBuyerMatrix()", "calculateCashOffer()"
      ],
      inputType: "number" as const,
      formatType: "currency" as const
    },
    {
      page: "Global",
      section: "Property Header",
      inputField: "Acquisitions Price",
      domId: "acquisitions-price",
      centralStateKey: "deal.acquisitionsPrice",
      consumingFormulas: ["globalAcquisitionsPrice", "compareAll", "profitCalculations"],
      updateFunctions: [
        "updateGlobalAcquisitionsPriceFromHeader()", "updateAllTabCalculations()",
        "recalculateDispositions()"
      ],
      inputType: "number" as const,
      formatType: "currency" as const
    }
  ] as InputBinding[],

  // ========================================
  // ACQUISITIONS SECTION
  // ========================================
  acquisitionsInputs: {
    
    // WHOLESALE STRATEGY
    wholesale: [
      {
        page: "Acq → Wholesale",
        section: "Offer Assumptions",
        inputField: "ARV Percentage Slider",
        domId: "wholesale-arv-percent",
        centralStateKey: "wholesale.arvPercent",
        consumingFormulas: ["wholesaleMAO", "ackermanOffers", "compareAll"],
        updateFunctions: ["recalculateWholesale()", "updateComparisonResults()"],
        inputType: "slider" as const,
        formatType: "percentage" as const
      },
      {
        page: "Acq → Wholesale",
        section: "Offer Assumptions", 
        inputField: "Assignment Fee",
        domId: "assignment-fee",
        centralStateKey: "wholesale.assignmentFee",
        consumingFormulas: ["wholesaleProfit", "ackermanOffers", "compareAll"],
        updateFunctions: ["recalculateWholesale()", "updateComparisonResults()"],
        inputType: "number" as const,
        formatType: "currency" as const
      }
    ] as InputBinding[],

    // INSTALLMENT/NOVATION STRATEGY
    installment: [
      {
        page: "Acq → Installment",
        section: "Equitable Deposit Structure",
        inputField: "Refundable Consideration",
        domId: "refundable-consideration",
        centralStateKey: "installment.refundableConsideration", 
        consumingFormulas: ["totalDeposit", "compareAll"],
        updateFunctions: ["recalculateInstallment()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Installment",
        section: "Equitable Deposit Structure",
        inputField: "Non-Refundable Costs",
        domId: "non-refundable-costs",
        centralStateKey: "installment.nonRefundableCosts",
        consumingFormulas: ["totalDeposit", "netProfit", "compareAll"],
        updateFunctions: ["recalculateInstallment()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Installment",
        section: "Local Control",
        inputField: "Minimum Acceptable Profit",
        domId: "minimum-acceptable-profit-local",
        centralStateKey: "installment.minimumAcceptableProfit",
        consumingFormulas: ["installmentMAO", "netProfit", "compareAll"],
        updateFunctions: ["recalculateInstallment()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      // Dynamic Fee Calculator (16 inputs)
      {
        page: "Acq → Installment",
        section: "Dynamic Fee Calculator",
        inputField: "Title Company Fee",
        domId: "title-company-fee",
        centralStateKey: "installment.fees.titleCompanyFee",
        consumingFormulas: ["totalInstallmentFees", "installmentMAO", "netToUs"], 
        updateFunctions: ["recalculateInstallment()", "recalculateNovationMAO()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Installment",
        section: "Dynamic Fee Calculator",
        inputField: "Listing Agent Commission %",
        domId: "listing-agent-commission",
        centralStateKey: "installment.fees.listingAgentCommission",
        consumingFormulas: ["totalInstallmentFees", "installmentMAO"],
        updateFunctions: ["recalculateInstallment()"],
        inputType: "number" as const,
        formatType: "percentage" as const
      },
      // ... (14 more fee inputs would be mapped here)
    ] as InputBinding[],

    // SUBJECT-TO STRATEGY
    subjectTo: [
      {
        page: "Acq → Subject-To",
        section: "Acquisition Inputs",
        inputField: "Existing Loan Balance",
        domId: "existing-loan-balance",
        centralStateKey: "subjectTo.existingLoanBalance",
        consumingFormulas: ["equityPosition", "cashFlow", "compareAll"],
        updateFunctions: ["recalculateSubjectTo()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Subject-To",
        section: "Acquisition Inputs",
        inputField: "Cash to Seller",
        domId: "cash-to-seller",
        centralStateKey: "subjectTo.cashToSeller",
        consumingFormulas: ["cashToClose", "totalInvestment", "compareAll"],
        updateFunctions: ["recalculateSubjectTo()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Subject-To",
        section: "Acquisition Inputs",
        inputField: "Arrears/Liens",
        domId: "arrears-liens", 
        centralStateKey: "subjectTo.arrearsLiens",
        consumingFormulas: ["cashToClose", "totalInvestment", "compareAll"],
        updateFunctions: ["recalculateSubjectTo()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Subject-To",
        section: "Acquisition Inputs",
        inputField: "Monthly PI",
        domId: "monthly-pi",
        centralStateKey: "subjectTo.monthlyPI",
        consumingFormulas: ["monthlyCashFlow", "annualCashFlow", "compareAll"],
        updateFunctions: ["recalculateSubjectTo()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Subject-To",
        section: "Acquisition Inputs",
        inputField: "Monthly Escrow (TI)",
        domId: "monthly-escrow",
        centralStateKey: "subjectTo.monthlyEscrow",
        consumingFormulas: ["monthlyCashFlow", "totalPITI", "compareAll"],
        updateFunctions: ["recalculateSubjectTo()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Subject-To",
        section: "Acquisition Inputs",
        inputField: "Interest Rate",
        domId: "interest-rate",
        centralStateKey: "subjectTo.interestRate", 
        consumingFormulas: ["paymentCalculation", "compareAll"],
        updateFunctions: ["recalculateSubjectTo()"],
        inputType: "number" as const,
        formatType: "percentage" as const
      }
    ] as InputBinding[],

    // SELLER FINANCE STRATEGY
    sellerFinance: [
      {
        page: "Acq → Seller Finance",
        section: "Three Key Offer Components",
        inputField: "Purchase Price",
        domId: "sf-purchase-price",
        centralStateKey: "sellerFinance.purchasePrice",
        consumingFormulas: ["loanAmount", "monthlyPayment", "compareAll"],
        updateFunctions: ["recalculateSellerFinance()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Seller Finance",
        section: "Three Key Offer Components",
        inputField: "Timeline (Years)",
        domId: "sf-timeline",
        centralStateKey: "sellerFinance.timelineYears",
        consumingFormulas: ["monthlyPayment", "balloonPayment", "compareAll"],
        updateFunctions: ["recalculateSellerFinance()"],
        inputType: "select" as const,
        formatType: "integer" as const
      },
      {
        page: "Acq → Seller Finance",
        section: "Three Key Offer Components",
        inputField: "Custom Monthly Payment Override",
        domId: "custom-monthly-payment",
        centralStateKey: "sellerFinance.customMonthlyPayment",
        consumingFormulas: ["cashFlow", "balloonCalculation", "compareAll"],
        updateFunctions: ["recalculateSellerFinance()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Acq → Seller Finance",
        section: "Market Analysis & Balloon Exit Strategy",
        inputField: "Year-over-Year Appreciation Rate",
        domId: "appreciation-rate",
        centralStateKey: "sellerFinance.appreciationRate",
        consumingFormulas: ["projectedPropertyValue", "balloonAnalysis"],
        updateFunctions: ["updateMarketAnalysis()"],
        inputType: "slider" as const,
        formatType: "percentage" as const
      },
      {
        page: "Acq → Seller Finance",
        section: "Market Analysis & Balloon Exit Strategy",
        inputField: "Balloon Year Selector",
        domId: "balloon-year",
        centralStateKey: "sellerFinance.balloonYear",
        consumingFormulas: ["projectedPropertyValue", "remainingBalance"],
        updateFunctions: ["updateMarketAnalysis()"],
        inputType: "select" as const,
        formatType: "integer" as const
      }
    ] as InputBinding[]
  },

  // ========================================
  // DISPOSITIONS SECTION
  // ========================================
  dispositionsInputs: {
    
    // GLOBAL DEAL VARIABLES
    globalDealVariables: [
      {
        page: "Dispo → Global",
        section: "Deal Variables",
        inputField: "Acquisition Cost",
        domId: "dispositions-acquisition-price",
        centralStateKey: "dispositions.acquisitionCost",
        consumingFormulas: ["allExitStrategies", "profitCalculations", "compareAll"],
        updateFunctions: ["recalculateDispositions()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Dispo → Global",
        section: "Deal Variables", 
        inputField: "PITI (Principal, Interest, Taxes, Insurance)",
        domId: "dispositions-piti",
        centralStateKey: "dispositions.piti",
        consumingFormulas: ["cashFlow", "subjectToWrap", "sellerFinanceWrap"],
        updateFunctions: ["recalculateDispositions()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Dispo → Global",
        section: "Deal Variables",
        inputField: "Closing Costs",
        domId: "dispositions-closing-costs",
        centralStateKey: "dispositions.closingCosts", 
        consumingFormulas: ["netProceeds", "profitCalculations"],
        updateFunctions: ["recalculateDispositions()"],
        inputType: "number" as const,
        formatType: "currency" as const
      }
    ] as InputBinding[],

    // CASH SALE TAB
    cashSale: [
      {
        page: "Dispo → Cash Sale",
        section: "Wholesale Exit Buyer Persona Matrix",
        inputField: "Max-Profit Flipper Percentage Slider",
        domId: "max-profit-flipper-slider",
        centralStateKey: "dispositions.maxProfitPercent",
        consumingFormulas: ["maxProfitFormula: ARV × sliderPercent - Repairs"],
        updateFunctions: ["updateWholesaleBuyerMatrix()"],
        inputType: "slider" as const,
        formatType: "percentage" as const
      }
    ] as InputBinding[],

    // MLS/NOVATION TAB
    mlsNovation: [
      {
        page: "Dispo → MLS/Novation",
        section: "Commission Analysis",
        inputField: "Listing Commission %",
        domId: "listing-commission",
        centralStateKey: "dispositions.listingCommission",
        consumingFormulas: ["netProceeds", "totalCommissions", "compareAll"],
        updateFunctions: ["updateNovationCalculation()"],
        inputType: "number" as const,
        formatType: "percentage" as const
      },
      {
        page: "Dispo → MLS/Novation",
        section: "Commission Analysis",
        inputField: "Buyer Agent Commission %", 
        domId: "buyer-agent-commission",
        centralStateKey: "dispositions.buyerAgentCommission",
        consumingFormulas: ["netProceeds", "totalCommissions", "compareAll"],
        updateFunctions: ["updateNovationCalculation()"],
        inputType: "number" as const,
        formatType: "percentage" as const
      }
    ] as InputBinding[],

    // SUBJECT-TO WRAP TAB
    subjectToWrap: [
      {
        page: "Dispo → Sub-To Wrap",
        section: "Cash-to-Close Builder",
        inputField: "Cash to Seller",
        domId: "cash-to-seller-dispo",
        centralStateKey: "dispositions.subTo.cashToSeller",
        consumingFormulas: ["cashToClose", "totalInvestment"],
        updateFunctions: ["formatAndRecalculateSubjectTo()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Dispo → Sub-To Wrap",
        section: "Cash-to-Close Builder",
        inputField: "Assignment Fee",
        domId: "assignment-fee-dispo",
        centralStateKey: "dispositions.subTo.assignmentFee",
        consumingFormulas: ["totalFees", "profit"],
        updateFunctions: ["formatAndRecalculateSubjectTo()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Dispo → Sub-To Wrap",
        section: "Cash-to-Close Builder",
        inputField: "Arrears/Liens",
        domId: "arrears-liens-dispo",
        centralStateKey: "dispositions.subTo.arrearsLiens",
        consumingFormulas: ["cashToClose", "totalInvestment"],
        updateFunctions: ["formatAndRecalculateSubjectTo()"],
        inputType: "number" as const,
        formatType: "currency" as const
      }
    ] as InputBinding[],

    // SELLER FINANCE WRAP / LEASE-OPTION TAB
    sfWrapLeaseOption: [
      {
        page: "Dispo → SF Wrap/Lease-Option",
        section: "Seller Finance Wrap Configurator",
        inputField: "Down Payment Percentage",
        domId: "wrap-down-payment-percent",
        centralStateKey: "dispositions.wrap.downPaymentPercent",
        consumingFormulas: ["downPaymentAmount", "loanAmount", "buyerPayment", "autoBuyerRate"],
        updateFunctions: ["updateWrapConfiguration()"],
        inputType: "slider" as const,
        formatType: "percentage" as const
      },
      {
        page: "Dispo → SF Wrap/Lease-Option",
        section: "Seller Finance Wrap Configurator",
        inputField: "Wrap Term (Years)",
        domId: "wrap-term",
        centralStateKey: "dispositions.wrap.termYears",
        consumingFormulas: ["buyerPayment", "amortizationSchedule"],
        updateFunctions: ["updateWrapConfiguration()"],
        inputType: "select" as const,
        formatType: "integer" as const
      },
      {
        page: "Dispo → SF Wrap/Lease-Option",
        section: "Lease-Option Sub-Buyer",
        inputField: "Equity Available",
        domId: "lease-option-equity",
        centralStateKey: "dispositions.leaseOption.equityAvailable",
        consumingFormulas: ["equityBonus", "targetCashToClose"],
        updateFunctions: ["formatAndRecalculateLeaseOption()"],
        inputType: "number" as const,
        formatType: "currency" as const
      },
      {
        page: "Dispo → SF Wrap/Lease-Option",
        section: "Lease-Option Sub-Buyer",
        inputField: "Repairs Needed",
        domId: "lease-option-repairs",
        centralStateKey: "dispositions.leaseOption.repairsNeeded",
        consumingFormulas: ["repairAdjustment", "targetCashToClose"],
        updateFunctions: ["formatAndRecalculateLeaseOption()"],
        inputType: "select" as const,
        formatType: "text" as const
      },
      {
        page: "Dispo → SF Wrap/Lease-Option",
        section: "Lease-Option Sub-Buyer",
        inputField: "Desired Cash Flow",
        domId: "lease-option-cash-flow",
        centralStateKey: "dispositions.leaseOption.desiredCashFlow",
        consumingFormulas: ["cashFlowBonus", "targetCashToClose"],
        updateFunctions: ["formatAndRecalculateLeaseOption()"],
        inputType: "number" as const,
        formatType: "currency" as const
      }
    ] as InputBinding[]
  },

  // ========================================
  // CALCULATION DEPENDENCIES
  // ========================================
  calculationDependencies: {
    // PRIMARY CALCULATIONS
    wholesaleMAO: {
      formula: "ARV × arvPercent - repairs - assignmentFee",
      dependencies: ["deal.arv", "deal.repairs", "wholesale.arvPercent", "wholesale.assignmentFee"],
      updateTriggers: ["recalculateWholesale()"]
    },
    installmentMAO: {
      formula: "ARV - repairs - discountToSellFast - totalCombinedFees - minimumAcceptableProfit",
      dependencies: ["deal.arv", "deal.repairs", "installment.fees", "installment.minimumAcceptableProfit"],
      updateTriggers: ["recalculateInstallment()", "recalculateNovationMAO()"]
    },
    subjectToCashFlow: {
      formula: "rent - monthlyPI - monthlyEscrow - repairsReserve",
      dependencies: ["deal.rent", "subjectTo.monthlyPI", "subjectTo.monthlyEscrow"],
      updateTriggers: ["recalculateSubjectTo()"]
    },
    sellerFinancePayment: {
      formula: "loanAmount × (monthlyRate × (1 + monthlyRate)^numPayments) / ((1 + monthlyRate)^numPayments - 1)",
      dependencies: ["sellerFinance.purchasePrice", "sellerFinance.interestRate", "sellerFinance.timelineYears"],
      updateTriggers: ["recalculateSellerFinance()"]
    },
    ackermanOffers: {
      formula: "65%, 85%, 95%, 100% of respective strategy MAO",
      dependencies: ["wholesaleMAO", "installmentMAO", "subjectToMAO", "sellerFinanceMAO"],
      updateTriggers: ["calculateAckermanOffers()"]
    },
    
    // DISPOSITIONS CALCULATIONS
    rentRuleInvestorPrice: {
      formula: "rent / 0.01",
      dependencies: ["deal.rent"],
      updateTriggers: ["updateWholesaleBuyerMatrix()"]
    },
    volumeFlipperPrice: {
      formula: "(ARV × 0.70) − repairs − $3,500",
      dependencies: ["deal.arv", "deal.repairs"],
      updateTriggers: ["updateWholesaleBuyerMatrix()"]
    },
    brrrInvestorPrice: {
      formula: "ARV × 0.70 - repairs",
      dependencies: ["deal.arv", "deal.repairs"],
      updateTriggers: ["updateWholesaleBuyerMatrix()"]
    },
    maxProfitFlipperPrice: {
      formula: "ARV × sliderPercent - repairs",
      dependencies: ["deal.arv", "deal.repairs", "dispositions.maxProfitPercent"],
      updateTriggers: ["updateWholesaleBuyerMatrix()"]
    },
    wrapBuyerPayment: {
      formula: "loanAmount × (monthlyRate × (1 + monthlyRate)^numPayments) / ((1 + monthlyRate)^numPayments - 1)",
      dependencies: ["deal.arv", "dispositions.wrap.downPaymentPercent", "dispositions.wrap.termYears"],
      updateTriggers: ["updateWrapConfiguration()"]
    },
    leaseOptionTargetCashToClose: {
      formula: "baseCashToClose + cashFlowBonus + equityBonus + repairAdjustment",
      dependencies: ["deal.arv", "dispositions.leaseOption.equityAvailable", "dispositions.leaseOption.desiredCashFlow", "dispositions.leaseOption.repairsNeeded"],
      updateTriggers: ["updateLeaseOptionCalculation()"]
    }
  } as Record<string, CalculationDependency>,

  // ========================================
  // UPDATE FUNCTION MAPPING
  // ========================================
  updateFunctionMap: {
    // GLOBAL UPDATE FUNCTIONS
    "updateAllTabCalculations()": [
      "recalculateWholesale()", "recalculateInstallment()", 
      "recalculateSubjectTo()", "recalculateSellerFinance()",
      "updateComparisonResults()"
    ],
    "recalculateDispositions()": [
      "updateWholesaleBuyerMatrix()", "updateNovationCalculation()",
      "formatAndRecalculateSubjectTo()", "updateWrapConfiguration()",
      "updateLeaseOptionCalculation()", "updateCompareAllStrategies()"
    ],

    // ACQUISITION FUNCTIONS
    "recalculateWholesale()": ["calculateAckermanOffers()", "updateComparisonResults()"],
    "recalculateInstallment()": ["recalculateNovationMAO()", "updateComparisonResults()"],
    "recalculateSubjectTo()": ["calculateCashOffer()", "updateComparisonResults()"],
    "recalculateSellerFinance()": ["updateMarketAnalysis()", "updateComparisonResults()"],

    // DISPOSITION FUNCTIONS
    "updateWholesaleBuyerMatrix()": ["updateCompareAllStrategies()"],
    "updateNovationCalculation()": ["updateCompareAllStrategies()"],
    "formatAndRecalculateSubjectTo()": ["updateCompareAllStrategies()"],
    "updateWrapConfiguration()": ["updateCompareAllStrategies()"],
    "updateLeaseOptionCalculation()": ["updateCompareAllStrategies()"]
  },

  // ========================================
  // STATE MANAGEMENT
  // ========================================
  stateManagement: {
    globalVariables: [
      "window.globalAcquisitionsPrice",
      "window.globalMinAcceptableProfit"
    ],
    sessionStorage: [
      "propertyData",
      "calculationResults", 
      "userPreferences"
    ],
    domState: [
      "activeTabStates",
      "inputFieldValues",
      "calculatedResultDisplays"
    ]
  },

  // ========================================
  // TESTING & VALIDATION
  // ========================================
  testingChecklist: {
    manualQA: [
      "Change ARV → All MAO calculations update across all tabs",
      "Change Repairs → All profit calculations update in real-time",
      "Change Rent → All cash flow calculations update instantly",
      "Modify commission sliders → Net proceeds update immediately",
      "Adjust down payment slider → Wrap calculations recalculate",
      "Switch between tabs → All values persist correctly",
      "Refresh page → Last input values restore properly",
      "Global variables sync between Acquisitions and Dispositions"
    ],
    consoleValidation: [
      "No JavaScript errors on any input change",
      "Functions called in correct dependency sequence",
      "Number formatting applied consistently",
      "Cross-tab synchronization working",
      "Memory leaks avoided in calculation loops"
    ]
  }
} as const;

// Type exports for external use
export type InputBindingType = typeof FORMULA_BINDING_MAP.globalInputs[0];
export type CalculationDependencyType = typeof FORMULA_BINDING_MAP.calculationDependencies.wholesaleMAO;