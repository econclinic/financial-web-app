export type Locale = "en" | "fa";

export const localeConfig: Record<Locale, { label: string; dir: "ltr" | "rtl" }> = {
  en: { label: "English", dir: "ltr" },
  fa: { label: "فارسی", dir: "rtl" },
};

const en = {
  // Navbar
  "nav.title": "Financial Dashboard",
  "nav.portfolio": "Portfolio",
  "nav.analytics": "Analytics",
  "nav.watchlist": "Watchlist",
  "nav.alerts": "Alerts",
  "nav.notifications": "Notifications",
  "nav.login": "Login",
  "nav.register": "Register",
  "nav.logout": "Logout",

  // Dashboard
  "dashboard.portfolioValue": "Portfolio Value",
  "dashboard.todaysChange": "Today's Change",
  "dashboard.totalReturn": "Total Return",
  "dashboard.positions": "Positions",
  "dashboard.marketData": "Market Data",
  "dashboard.marketDataError": "Could not load market data. Make sure the backend is running.",
  "dashboard.loadingMarket": "Loading market data...",
  "dashboard.priceHistory": "{symbol} — 30 Day Price History",

  // Analytics
  "analytics.title": "Portfolio Analytics",
  "analytics.totalValue": "Total Value",
  "analytics.todaysChange": "Today's Change",
  "analytics.totalPnl": "Total P&L",
  "analytics.costBasis": "Cost Basis",
  "analytics.allocationByClass": "Allocation by Asset Class",
  "analytics.allocationBySymbol": "Allocation by Symbol",
  "analytics.performance": "Portfolio Performance",
  "analytics.topGainers": "Top Gainers",
  "analytics.topLosers": "Top Losers",
  "analytics.noData": "No portfolio data. Add transactions to see analytics.",
  "analytics.loading": "Loading analytics...",
  "analytics.noHistory": "No history data available.",

  // Portfolio
  "portfolio.title": "Portfolio",
  "portfolio.newTransaction": "New Transaction",
  "portfolio.totalValue": "Total Value",
  "portfolio.totalInvested": "Total Invested",
  "portfolio.totalPnl": "Total P&L",
  "portfolio.return": "Return",
  "portfolio.positions": "Positions",
  "portfolio.allocation": "Portfolio Allocation",
  "portfolio.transactionHistory": "Transaction History",
  "portfolio.noPositions": "No positions yet. Add your first transaction to get started.",
  "portfolio.loading": "Loading portfolio...",
  "portfolio.symbol": "Symbol",
  "portfolio.type": "Type",
  "portfolio.quantity": "Quantity",
  "portfolio.avgPrice": "Avg Price",
  "portfolio.currentPrice": "Current Price",
  "portfolio.value": "Value",
  "portfolio.pnl": "P&L",
  "portfolio.date": "Date",
  "portfolio.price": "Price",
  "portfolio.total": "Total",
  "portfolio.live": "Live",
  "portfolio.priceError": "— showing last cached prices.",

  // New Transaction
  "newTransaction.title": "New Transaction",
  "newTransaction.back": "Back to Portfolio",
  "newTransaction.symbol": "Symbol",
  "newTransaction.assetType": "Asset Type",
  "newTransaction.transactionType": "Transaction Type",
  "newTransaction.quantity": "Quantity",
  "newTransaction.price": "Price per Unit ($)",
  "newTransaction.submit": "Create Transaction",
  "newTransaction.submitting": "Creating…",
  "newTransaction.crypto": "crypto",
  "newTransaction.stock": "stock",
  "newTransaction.buy": "buy",
  "newTransaction.sell": "sell",

  // Alerts
  "alerts.title": "Price Alerts",
  "alerts.symbol": "Symbol",
  "alerts.direction": "Direction",
  "alerts.above": "Above",
  "alerts.below": "Below",
  "alerts.targetPrice": "Target Price ($)",
  "alerts.create": "Create Alert",
  "alerts.delete": "Delete",
  "alerts.condition": "Condition",
  "alerts.status": "Status",
  "alerts.triggeredAt": "Triggered At",
  "alerts.actions": "Actions",
  "alerts.active": "Active",
  "alerts.triggered": "Triggered",
  "alerts.noAlerts": "No alerts set.",
  "alerts.noAlertsHint": "Create an alert above to get started.",
  "alerts.loading": "Loading alerts...",

  // Watchlist
  "watchlist.title": "Watchlist",
  "watchlist.add": "Add",
  "watchlist.remove": "Remove",
  "watchlist.placeholder": "Enter symbol (e.g. BTC)",
  "watchlist.currentPrice": "Current Price",
  "watchlist.change24h": "24h Change",
  "watchlist.actions": "Actions",
  "watchlist.empty": "Your watchlist is empty.",
  "watchlist.emptyHint": "Add a symbol above to start tracking.",
  "watchlist.loading": "Loading watchlist...",

  // Notifications
  "notifications.title": "Notifications",
  "notifications.markAllRead": "Mark all as read",
  "notifications.markRead": "Mark as read",
  "notifications.empty": "No notifications.",
  "notifications.emptyHint": "Notifications will appear here when your price alerts are triggered.",
  "notifications.loading": "Loading notifications...",

  // Auth
  "auth.signIn": "Sign In",
  "auth.signInDesc": "Enter your credentials to access the dashboard",
  "auth.email": "Email",
  "auth.password": "Password",
  "auth.signingIn": "Signing in…",
  "auth.noAccount": "Don't have an account?",
  "auth.createAccount": "Create Account",
  "auth.createAccountDesc": "Register to access the financial dashboard",
  "auth.confirmPassword": "Confirm Password",
  "auth.creatingAccount": "Creating account…",
  "auth.hasAccount": "Already have an account?",
  "auth.signInLink": "Sign in",
  "auth.registerLink": "Register",

  // Smart Summary
  "summary.title": "Market Insights",
  "summary.marketTrend": "Avg. Daily Change",
  "summary.combined": "combined",
  "summary.bestPerformer": "Best Performer",
  "summary.worstPerformer": "Worst Performer",

  // Common
  "common.loading": "Loading...",
  "common.error": "Error",
} as const;

const fa: Record<keyof typeof en, string> = {
  // Navbar
  "nav.title": "داشبورد مالی",
  "nav.portfolio": "سبد دارایی",
  "nav.analytics": "تحلیل‌ها",
  "nav.watchlist": "لیست نظارت",
  "nav.alerts": "هشدارها",
  "nav.notifications": "اعلان‌ها",
  "nav.login": "ورود",
  "nav.register": "ثبت‌نام",
  "nav.logout": "خروج",

  // Dashboard
  "dashboard.portfolioValue": "ارزش سبد",
  "dashboard.todaysChange": "تغییر امروز",
  "dashboard.totalReturn": "بازده کل",
  "dashboard.positions": "موقعیت‌ها",
  "dashboard.marketData": "داده‌های بازار",
  "dashboard.marketDataError": "بارگذاری داده‌های بازار ناموفق بود. مطمئن شوید بک‌اند در حال اجرا است.",
  "dashboard.loadingMarket": "بارگذاری داده‌های بازار...",
  "dashboard.priceHistory": "{symbol} — تاریخچه ۳۰ روزه قیمت",

  // Analytics
  "analytics.title": "تحلیل سبد دارایی",
  "analytics.totalValue": "ارزش کل",
  "analytics.todaysChange": "تغییر امروز",
  "analytics.totalPnl": "سود و زیان کل",
  "analytics.costBasis": "قیمت تمام‌شده",
  "analytics.allocationByClass": "تخصیص بر اساس نوع دارایی",
  "analytics.allocationBySymbol": "تخصیص بر اساس نماد",
  "analytics.performance": "عملکرد سبد دارایی",
  "analytics.topGainers": "بیشترین رشد",
  "analytics.topLosers": "بیشترین افت",
  "analytics.noData": "داده‌ای برای سبد دارایی وجود ندارد. تراکنش‌ها را اضافه کنید.",
  "analytics.loading": "بارگذاری تحلیل‌ها...",
  "analytics.noHistory": "داده تاریخچه‌ای موجود نیست.",

  // Portfolio
  "portfolio.title": "سبد دارایی",
  "portfolio.newTransaction": "تراکنش جدید",
  "portfolio.totalValue": "ارزش کل",
  "portfolio.totalInvested": "سرمایه‌گذاری کل",
  "portfolio.totalPnl": "سود و زیان کل",
  "portfolio.return": "بازده",
  "portfolio.positions": "موقعیت‌ها",
  "portfolio.allocation": "تخصیص سبد دارایی",
  "portfolio.transactionHistory": "تاریخچه تراکنش‌ها",
  "portfolio.noPositions": "هنوز موقعیتی ندارید. اولین تراکنش خود را اضافه کنید.",
  "portfolio.loading": "بارگذاری سبد دارایی...",
  "portfolio.symbol": "نماد",
  "portfolio.type": "نوع",
  "portfolio.quantity": "تعداد",
  "portfolio.avgPrice": "قیمت میانگین",
  "portfolio.currentPrice": "قیمت فعلی",
  "portfolio.value": "ارزش",
  "portfolio.pnl": "سود/زیان",
  "portfolio.date": "تاریخ",
  "portfolio.price": "قیمت",
  "portfolio.total": "مجموع",
  "portfolio.live": "زنده",
  "portfolio.priceError": "— نمایش آخرین قیمت‌های ذخیره‌شده.",

  // New Transaction
  "newTransaction.title": "تراکنش جدید",
  "newTransaction.back": "بازگشت به سبد دارایی",
  "newTransaction.symbol": "نماد",
  "newTransaction.assetType": "نوع دارایی",
  "newTransaction.transactionType": "نوع تراکنش",
  "newTransaction.quantity": "تعداد",
  "newTransaction.price": "قیمت واحد ($)",
  "newTransaction.submit": "ایجاد تراکنش",
  "newTransaction.submitting": "در حال ایجاد…",
  "newTransaction.crypto": "رمزارز",
  "newTransaction.stock": "سهام",
  "newTransaction.buy": "خرید",
  "newTransaction.sell": "فروش",

  // Alerts
  "alerts.title": "هشدارهای قیمت",
  "alerts.symbol": "نماد",
  "alerts.direction": "جهت",
  "alerts.above": "بالاتر از",
  "alerts.below": "پایین‌تر از",
  "alerts.targetPrice": "قیمت هدف ($)",
  "alerts.create": "ایجاد هشدار",
  "alerts.delete": "حذف",
  "alerts.condition": "شرط",
  "alerts.status": "وضعیت",
  "alerts.triggeredAt": "زمان فعال‌سازی",
  "alerts.actions": "عملیات",
  "alerts.active": "فعال",
  "alerts.triggered": "فعال شده",
  "alerts.noAlerts": "هشداری تنظیم نشده.",
  "alerts.noAlertsHint": "یک هشدار در بالا ایجاد کنید.",
  "alerts.loading": "بارگذاری هشدارها...",

  // Watchlist
  "watchlist.title": "لیست نظارت",
  "watchlist.add": "افزودن",
  "watchlist.remove": "حذف",
  "watchlist.placeholder": "نماد وارد کنید (مثلاً BTC)",
  "watchlist.currentPrice": "قیمت فعلی",
  "watchlist.change24h": "تغییر ۲۴ ساعته",
  "watchlist.actions": "عملیات",
  "watchlist.empty": "لیست نظارت شما خالی است.",
  "watchlist.emptyHint": "یک نماد در بالا اضافه کنید.",
  "watchlist.loading": "بارگذاری لیست نظارت...",

  // Notifications
  "notifications.title": "اعلان‌ها",
  "notifications.markAllRead": "خواندن همه",
  "notifications.markRead": "خوانده شد",
  "notifications.empty": "اعلانی وجود ندارد.",
  "notifications.emptyHint": "اعلان‌ها هنگام فعال شدن هشدارهای قیمت اینجا نمایش داده می‌شوند.",
  "notifications.loading": "بارگذاری اعلان‌ها...",

  // Auth
  "auth.signIn": "ورود",
  "auth.signInDesc": "اطلاعات ورود خود را وارد کنید",
  "auth.email": "ایمیل",
  "auth.password": "رمز عبور",
  "auth.signingIn": "در حال ورود…",
  "auth.noAccount": "حساب کاربری ندارید؟",
  "auth.createAccount": "ایجاد حساب",
  "auth.createAccountDesc": "برای دسترسی به داشبورد مالی ثبت‌نام کنید",
  "auth.confirmPassword": "تأیید رمز عبور",
  "auth.creatingAccount": "در حال ایجاد حساب…",
  "auth.hasAccount": "قبلاً حساب دارید؟",
  "auth.signInLink": "ورود",
  "auth.registerLink": "ثبت‌نام",

  // Smart Summary
  "summary.title": "بینش بازار",
  "summary.marketTrend": "میانگین تغییر روزانه",
  "summary.combined": "مجموع",
  "summary.bestPerformer": "بهترین عملکرد",
  "summary.worstPerformer": "ضعیف‌ترین عملکرد",

  // Common
  "common.loading": "بارگذاری...",
  "common.error": "خطا",
};

export type TranslationKey = keyof typeof en;

const translations: Record<Locale, Record<TranslationKey, string>> = { en, fa };

export function t(locale: Locale, key: TranslationKey, params?: Record<string, string>): string {
  let value = translations[locale][key] ?? translations.en[key] ?? key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      value = value.replace(`{${k}}`, v);
    }
  }
  return value;
}
