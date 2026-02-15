import React, { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Link, useNavigate, Navigate, useLocation } from "react-router-dom";
import axios from "axios";
import { 
  Upload, FileText, CheckCircle, XCircle, AlertCircle, List, Settings, Home, 
  Moon, Sun, Users, Key, LogOut, CreditCard, Zap, Shield, Clock, Menu, X,
  BarChart3, Archive, ChevronDown, ChevronRight, Plus, Trash2, Edit, Eye, EyeOff,
  Phone, Building, Mail, User, Lock, Globe, Search as SearchIcon, LayoutDashboard,
  Banknote
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import translations from "./translations";
import { PaymentPage, PaymentSuccessPage, PaymentPendingPage, PaymentCancelPage } from "./pages/PaymentPage";
import { AdminPayments } from "./pages/Admin/AdminPayments";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BRANCHES = ["Bursa", "İzmit", "Orhanlı", "Hadımköy", "Keşan"];

// ==================== LANGUAGE CONTEXT ====================

const LanguageContext = createContext();

const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => localStorage.getItem("language") || "tr");
  const [siteSettings, setSiteSettings] = useState(null);

  useEffect(() => {
    localStorage.setItem("language", language);
    document.documentElement.lang = language;
  }, [language]);

  useEffect(() => {
    fetchSiteSettings();
  }, []);

  const fetchSiteSettings = async () => {
    try {
      const response = await axios.get(`${API}/site-settings`);
      setSiteSettings(response.data);
      if (response.data.default_language && !localStorage.getItem("language")) {
        setLanguage(response.data.default_language);
      }
    } catch (error) {
      console.error("Site settings yüklenemedi:", error);
    }
  };

  const t = (key) => translations[language]?.[key] || translations.tr[key] || key;

  const toggleLanguage = () => setLanguage(language === "tr" ? "en" : "tr");

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage, t, siteSettings, fetchSiteSettings }}>
      {children}
    </LanguageContext.Provider>
  );
};

const useLanguage = () => useContext(LanguageContext);

// ==================== AUTH CONTEXT ====================

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(response.data);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (data) => {
    const response = await axios.post(`${API}/auth/register`, data);
    const { access_token, user: userData } = response.data;
    localStorage.setItem("token", access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading, fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

// ==================== THEME CONTEXT ====================

const ThemeContext = createContext();

const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme(theme === "light" ? "dark" : "light");

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

const useTheme = () => useContext(ThemeContext);

// ==================== SEO HEAD COMPONENT ====================

const SEOHead = () => {
  const { siteSettings } = useLanguage();

  useEffect(() => {
    if (siteSettings) {
      document.title = siteSettings.meta_title || siteSettings.site_title || "IZE Case Resolver";
      
      // Meta tags
      updateMetaTag("description", siteSettings.meta_description);
      updateMetaTag("keywords", siteSettings.meta_keywords);
      updateMetaTag("author", siteSettings.meta_author);
      
      // Open Graph
      updateMetaTag("og:title", siteSettings.meta_title, "property");
      updateMetaTag("og:description", siteSettings.meta_description, "property");
      if (siteSettings.og_image_url) {
        updateMetaTag("og:image", siteSettings.og_image_url, "property");
      }
      
      // Analytics scripts
      if (siteSettings.google_analytics_id) {
        loadGoogleAnalytics(siteSettings.google_analytics_id);
      }
      if (siteSettings.yandex_metrica_id) {
        loadYandexMetrica(siteSettings.yandex_metrica_id);
      }
      if (siteSettings.google_tag_manager_id) {
        loadGoogleTagManager(siteSettings.google_tag_manager_id);
      }
    }
  }, [siteSettings]);

  return null;
};

const updateMetaTag = (name, content, attr = "name") => {
  if (!content) return;
  let element = document.querySelector(`meta[${attr}="${name}"]`);
  if (!element) {
    element = document.createElement("meta");
    element.setAttribute(attr, name);
    document.head.appendChild(element);
  }
  element.setAttribute("content", content);
};

const loadGoogleAnalytics = (id) => {
  if (document.getElementById("ga-script")) return;
  const script = document.createElement("script");
  script.id = "ga-script";
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${id}`;
  document.head.appendChild(script);
  
  window.dataLayer = window.dataLayer || [];
  function gtag(){window.dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', id);
};

const loadYandexMetrica = (id) => {
  if (document.getElementById("ym-script")) return;
  const script = document.createElement("script");
  script.id = "ym-script";
  script.innerHTML = `
    (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
    m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
    (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
    ym(${id}, "init", { clickmap:true, trackLinks:true, accurateTrackBounce:true });
  `;
  document.head.appendChild(script);
};

const loadGoogleTagManager = (id) => {
  if (document.getElementById("gtm-script")) return;
  const script = document.createElement("script");
  script.id = "gtm-script";
  script.innerHTML = `
    (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
    new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','${id}');
  `;
  document.head.appendChild(script);
};

// ==================== PROTECTED ROUTE ====================

const PrivateRoute = ({ children, adminOnly = false }) => {
  const { user, loading } = useAuth();
  const { t } = useLanguage();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && user.role !== "admin") {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// ==================== LANGUAGE SWITCHER ====================

const LanguageSwitcher = ({ className = "" }) => {
  const { language, toggleLanguage } = useLanguage();
  
  return (
    <Button variant="ghost" size="sm" onClick={toggleLanguage} className={className}>
      <Globe className="w-4 h-4 mr-1" />
      {language.toUpperCase()}
    </Button>
  );
};

// ==================== LANDING PAGE ====================

const LandingPage = () => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { t, siteSettings } = useLanguage();
  const navigate = useNavigate();

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-950 dark:to-gray-900">
      <nav className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <FileText className="w-8 h-8 text-primary" />
              <span className="text-xl font-bold">{siteSettings?.site_name || t("appName")}</span>
            </div>
            <div className="flex items-center gap-3">
              <LanguageSwitcher />
              <Button variant="ghost" size="sm" onClick={toggleTheme} data-testid="theme-toggle">
                {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              </Button>
              <Button variant="ghost" onClick={() => navigate("/login")} data-testid="login-btn">
                {t("login")}
              </Button>
              <Button onClick={() => navigate("/register")} data-testid="register-btn">
                {t("register")}
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-4" variant="outline">
            <Zap className="w-3 h-3 mr-1" />
            {t("freeTrialBadge")}
          </Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
            {t("heroTitle")}
          </h1>
          <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
            {siteSettings?.site_description || t("heroSubtitle")}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" onClick={() => navigate("/register")} data-testid="cta-register">
              {t("getStarted")}
              <CheckCircle className="ml-2 w-5 h-5" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate("/pricing")} data-testid="cta-pricing">
              {t("pricing")}
            </Button>
          </div>
        </div>
      </section>

      <section className="py-20 px-4 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12">{t("features")}</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <Upload className="w-10 h-10 text-primary mb-2" />
                <CardTitle>{t("featurePdfTitle")}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">{t("featurePdfDesc")}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <Shield className="w-10 h-10 text-primary mb-2" />
                <CardTitle>{t("featureWarrantyTitle")}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">{t("featureWarrantyDesc")}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <Clock className="w-10 h-10 text-primary mb-2" />
                <CardTitle>{t("featureSpeedTitle")}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">{t("featureSpeedDesc")}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <footer className="border-t py-8 px-4">
        <div className="max-w-7xl mx-auto text-center text-gray-600 dark:text-gray-400">
          <p>{siteSettings?.footer_text || `© 2026 ${t("appName")}. ${t("allRightsReserved")}`}</p>
        </div>
      </footer>
    </div>
  );
};

// ==================== LOGIN PAGE ====================

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, user } = useAuth();
  const { t, siteSettings } = useLanguage();
  const navigate = useNavigate();

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || t("loginError"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
      <Card className="w-full max-w-md" data-testid="login-card">
        <CardHeader className="text-center">
          <FileText className="w-12 h-12 mx-auto mb-2 text-primary" />
          <CardTitle className="text-2xl">{t("login")}</CardTitle>
          <CardDescription>{siteSettings?.site_name || t("appName")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>{t("email")}</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="ornek@email.com"
                data-testid="login-email"
              />
            </div>
            <div>
              <Label>{t("password")}</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="********"
                data-testid="login-password"
              />
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full" disabled={loading} data-testid="login-submit">
              {loading ? t("loading") : t("login")}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            {t("noAccount")}{" "}
            <Link to="/register" className="text-primary hover:underline">{t("register")}</Link>
          </div>
          <div className="mt-2 text-center">
            <Link to="/" className="text-sm text-gray-500 hover:underline">{t("backToHome")}</Link>
          </div>
          <div className="mt-4 flex justify-center">
            <LanguageSwitcher />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== REGISTER PAGE ====================

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    email: "", password: "", confirmPassword: "", full_name: "", phone_number: "", branch: ""
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { register, user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError(t("password") + " " + t("error"));
      return;
    }

    setLoading(true);

    try {
      await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        phone_number: formData.phone_number,
        branch: formData.branch,
        role: "user"
      });
      navigate("/dashboard");
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map(d => d.msg).join(", "));
      } else {
        setError(detail || t("error"));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4 py-8">
      <Card className="w-full max-w-md" data-testid="register-card">
        <CardHeader className="text-center">
          <FileText className="w-12 h-12 mx-auto mb-2 text-primary" />
          <CardTitle className="text-2xl">{t("register")}</CardTitle>
          <CardDescription>
            <Badge variant="outline" className="mt-2">
              <Zap className="w-3 h-3 mr-1" />
              {t("freeTrialBadge")}
            </Badge>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label className="flex items-center gap-1"><User className="w-4 h-4" /> {t("fullName")} *</Label>
              <Input type="text" name="full_name" value={formData.full_name} onChange={handleChange} required placeholder={t("fullName")} data-testid="register-fullname" />
            </div>
            <div>
              <Label className="flex items-center gap-1"><Mail className="w-4 h-4" /> {t("email")} *</Label>
              <Input type="email" name="email" value={formData.email} onChange={handleChange} required placeholder="ornek@email.com" data-testid="register-email" />
            </div>
            <div>
              <Label className="flex items-center gap-1"><Phone className="w-4 h-4" /> {t("phone")}</Label>
              <Input type="tel" name="phone_number" value={formData.phone_number} onChange={handleChange} placeholder="5XX XXX XXXX" data-testid="register-phone" />
            </div>
            <div>
              <Label className="flex items-center gap-1"><Building className="w-4 h-4" /> {t("branch")}</Label>
              <Select value={formData.branch} onValueChange={(value) => setFormData({...formData, branch: value})}>
                <SelectTrigger data-testid="register-branch"><SelectValue placeholder={t("branch")} /></SelectTrigger>
                <SelectContent>
                  {BRANCHES.map(b => (<SelectItem key={b} value={b}>{b}</SelectItem>))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="flex items-center gap-1"><Lock className="w-4 h-4" /> {t("password")} *</Label>
              <div className="relative">
                <Input type={showPassword ? "text" : "password"} name="password" value={formData.password} onChange={handleChange} required placeholder="********" data-testid="register-password" />
                <Button type="button" variant="ghost" size="sm" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
              <p className="text-xs text-gray-500 mt-1">{t("passwordRequirements")}</p>
            </div>
            <div>
              <Label>{t("confirmPassword")} *</Label>
              <Input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} required placeholder="********" data-testid="register-confirm-password" />
            </div>
            {error && (<Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>)}
            <Button type="submit" className="w-full" disabled={loading} data-testid="register-submit">
              {loading ? t("loading") : t("register")}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            {t("hasAccount")}{" "}<Link to="/login" className="text-primary hover:underline">{t("login")}</Link>
          </div>
          <div className="mt-4 flex justify-center"><LanguageSwitcher /></div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== PRICING PAGE ====================

const PricingPage = () => {
  const navigate = useNavigate();
  const { t, siteSettings } = useLanguage();
  const { theme, toggleTheme } = useTheme();

  const faqs = [
    { question: t("faqQuestion1"), answer: t("faqAnswer1") },
    { question: t("faqQuestion2"), answer: t("faqAnswer2") },
    { question: t("faqQuestion3"), answer: t("faqAnswer3") },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <nav className="border-b bg-white dark:bg-gray-900 px-4 py-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <FileText className="w-8 h-8 text-primary" />
            <span className="text-xl font-bold">{siteSettings?.site_name || t("appName")}</span>
          </Link>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <Button variant="ghost" size="sm" onClick={toggleTheme}>
              {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </Button>
            <Button variant="ghost" onClick={() => navigate("/")}>{t("backToHome")}</Button>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <Badge className="mb-4" variant="outline">
            <Zap className="w-3 h-3 mr-1" />
            {t("freeTrialBadge")}
          </Badge>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">{t("pricingTitle")}</h1>
          <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">{t("pricingSubtitle")}</p>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 mb-20">
          {/* Free Plan */}
          <Card className="border-2 relative">
            <CardHeader className="pb-2">
              <CardTitle className="text-xl">{t("free")}</CardTitle>
              <CardDescription>{t("freeDesc")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-baseline">
                <span className="text-4xl font-bold">0₺</span>
                <span className="text-gray-500 ml-1">{t("perMonth")}</span>
              </div>
              <Separator />
              <ul className="space-y-3">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>{t("freeAnalyses")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>{t("pdfReading")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>{t("aiAnalysis")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>{t("emailDraftFeature")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>{t("emailSupport")}</span>
                </li>
              </ul>
              <Button className="w-full" onClick={() => navigate("/register")} data-testid="pricing-free-btn">
                {t("startFree")}
              </Button>
            </CardContent>
          </Card>

          {/* Pro Plan */}
          <Card className="border-2 border-primary relative shadow-lg scale-105">
            <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
              <Badge className="bg-primary text-white px-4 py-1">{t("mostPopular")}</Badge>
            </div>
            <CardHeader className="pb-2 pt-8">
              <CardTitle className="text-xl">{t("pro")}</CardTitle>
              <CardDescription>{t("proDesc")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-baseline">
                <span className="text-4xl font-bold">{t("comingSoon")}</span>
              </div>
              <Separator />
              <ul className="space-y-3">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-primary flex-shrink-0" />
                  <span>{t("unlimitedAnalyses")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-primary flex-shrink-0" />
                  <span>{t("pdfReading")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-primary flex-shrink-0" />
                  <span>{t("aiAnalysis")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-primary flex-shrink-0" />
                  <span>{t("prioritySupport")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-primary flex-shrink-0" />
                  <span>{t("customReports")}</span>
                </li>
              </ul>
              <Button className="w-full" disabled>
                {t("comingSoon")}
              </Button>
            </CardContent>
          </Card>

          {/* Enterprise Plan */}
          <Card className="border-2 relative">
            <CardHeader className="pb-2">
              <CardTitle className="text-xl">{t("enterprise")}</CardTitle>
              <CardDescription>{t("enterpriseDesc")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-baseline">
                <span className="text-4xl font-bold">{t("customPricing")}</span>
              </div>
              <Separator />
              <ul className="space-y-3">
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  <span>{t("unlimitedAnalyses")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  <span>{t("dedicatedSupport")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  <span>{t("customIntegration")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  <span>{t("slaGuarantee")}</span>
                </li>
                <li className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  <span>{t("apiAccess")}</span>
                </li>
              </ul>
              <Button className="w-full" variant="outline" disabled>
                {t("contactSales")}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* FAQ Section */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-8">{t("faq")}</h2>
          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <Card key={index}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base font-medium flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-primary" />
                    {faq.question}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 dark:text-gray-400">{faq.answer}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t py-8 px-4">
        <div className="max-w-7xl mx-auto text-center text-gray-600 dark:text-gray-400">
          <p>{siteSettings?.footer_text || `© 2026 ${t("appName")}. ${t("allRightsReserved")}`}</p>
        </div>
      </footer>
    </div>
  );
};

// ==================== DASHBOARD ROUTER ====================

const DashboardRouter = () => {
  const { user } = useAuth();
  if (!user) return null;
  return user.role === "admin" ? <Navigate to="/admin/dashboard" replace /> : <Navigate to="/user/upload" replace />;
};

// ==================== ADMIN LAYOUT ====================

const AdminLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { t, siteSettings } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const menuItems = [
    { path: "/admin/dashboard", icon: BarChart3, label: t("dashboard") },
    { path: "/admin/users", icon: Users, label: t("users") },
    { path: "/admin/cases", icon: List, label: t("allCases") },
    { path: "/admin/rules", icon: FileText, label: t("warrantyRules") },
    { path: "/admin/api-settings", icon: Key, label: t("apiSettings") },
    { path: "/admin/email-settings", icon: Mail, label: t("emailSettings") },
    { path: "/admin/site-settings", icon: Settings, label: t("siteSettings") },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Mobile Header */}
      <div className="lg:hidden bg-white dark:bg-gray-900 border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-6 h-6 text-primary" />
          <span className="font-bold">{t("adminPanel")}</span>
        </div>
        <Button variant="ghost" size="sm" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </Button>
      </div>

      {mobileMenuOpen && (
        <div className="lg:hidden bg-white dark:bg-gray-900 border-b px-4 py-4 space-y-2">
          {menuItems.map((item) => (
            <Button key={item.path} variant={isActive(item.path) ? "secondary" : "ghost"} className="w-full justify-start" onClick={() => { navigate(item.path); setMobileMenuOpen(false); }}>
              <item.icon className="w-4 h-4 mr-2" />{item.label}
            </Button>
          ))}
          <Separator />
          <LanguageSwitcher className="w-full justify-start" />
          <Button variant="ghost" className="w-full justify-start" onClick={toggleTheme}>
            {theme === "light" ? <Moon className="w-4 h-4 mr-2" /> : <Sun className="w-4 h-4 mr-2" />}
            {theme === "light" ? t("darkMode") : t("lightMode")}
          </Button>
          <Button variant="ghost" className="w-full justify-start text-red-500" onClick={logout}>
            <LogOut className="w-4 h-4 mr-2" />{t("logout")}
          </Button>
        </div>
      )}

      <div className="flex">
        <aside className={`hidden lg:block ${sidebarOpen ? 'w-64' : 'w-16'} bg-white dark:bg-gray-900 border-r min-h-screen transition-all duration-300`}>
          <div className="p-4 border-b flex items-center justify-between">
            {sidebarOpen && (
              <div className="flex items-center gap-2">
                <FileText className="w-8 h-8 text-primary" />
                <span className="font-bold">{t("adminPanel")}</span>
              </div>
            )}
            <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(!sidebarOpen)}>
              {sidebarOpen ? <ChevronDown className="w-4 h-4 rotate-90" /> : <ChevronRight className="w-4 h-4" />}
            </Button>
          </div>
          <nav className="p-4 space-y-2">
            {menuItems.map((item) => (
              <Button key={item.path} variant={isActive(item.path) ? "secondary" : "ghost"} className={`w-full ${sidebarOpen ? 'justify-start' : 'justify-center'}`} onClick={() => navigate(item.path)} data-testid={`nav-${item.path.split('/').pop()}`}>
                <item.icon className="w-4 h-4" />{sidebarOpen && <span className="ml-2">{item.label}</span>}
              </Button>
            ))}
            <Separator className="my-4" />
            {sidebarOpen && <LanguageSwitcher className="w-full justify-start" />}
            <Button variant="ghost" className={`w-full ${sidebarOpen ? 'justify-start' : 'justify-center'}`} onClick={toggleTheme}>
              {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              {sidebarOpen && <span className="ml-2">{theme === "light" ? t("darkMode") : t("lightMode")}</span>}
            </Button>
            <Button variant="ghost" className={`w-full ${sidebarOpen ? 'justify-start' : 'justify-center'} text-red-500`} onClick={logout}>
              <LogOut className="w-4 h-4" />{sidebarOpen && <span className="ml-2">{t("logout")}</span>}
            </Button>
          </nav>
        </aside>

        <main className="flex-1 p-4 lg:p-8">
          <div className="mb-6">
            <p className="text-sm text-gray-500">{t("welcomeAdmin")}, <strong>{user?.full_name}</strong> ({t("admin")})</p>
          </div>
          {children}
        </main>
      </div>
    </div>
  );
};

// ==================== USER LAYOUT ====================

const UserLayout = ({ children }) => {
  const { user, logout, fetchUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { t, siteSettings } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => { fetchUser(); }, []);

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <nav className="bg-white dark:bg-gray-900 border-b px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <FileText className="w-6 sm:w-8 h-6 sm:h-8 text-primary" />
              <span className="font-bold hidden sm:inline">{siteSettings?.site_name || t("appName")}</span>
            </div>
            <div className="hidden sm:flex gap-2">
              <Button variant={isActive("/user/upload") ? "secondary" : "ghost"} size="sm" onClick={() => navigate("/user/upload")} data-testid="nav-upload">
                <Upload className="w-4 h-4 mr-2" />{t("uploadIze")}
              </Button>
              <Button variant={isActive("/user/cases") ? "secondary" : "ghost"} size="sm" onClick={() => navigate("/user/cases")} data-testid="nav-cases">
                <List className="w-4 h-4 mr-2" />{t("myAnalyses")}
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <Badge variant="outline" className="text-xs sm:text-sm">
              <CreditCard className="w-3 h-3 mr-1" />
              <span className="hidden sm:inline">{t("credit")}:</span> {user?.free_analyses_remaining || 0}
            </Badge>
            <LanguageSwitcher className="hidden sm:inline-flex" />
            <Button variant="ghost" size="sm" onClick={toggleTheme} className="hidden sm:inline-flex">
              {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </Button>
            <Button variant="ghost" size="sm" onClick={logout} className="hidden sm:inline-flex" data-testid="logout-btn">
              <LogOut className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="sm:hidden">
              <Menu className="w-5 h-5" />
            </Button>
          </div>
        </div>
        
        {mobileMenuOpen && (
          <div className="sm:hidden mt-3 pt-3 border-t space-y-2">
            <Button variant="ghost" className="w-full justify-start" onClick={() => { navigate("/user/upload"); setMobileMenuOpen(false); }}>
              <Upload className="w-4 h-4 mr-2" />{t("uploadIze")}
            </Button>
            <Button variant="ghost" className="w-full justify-start" onClick={() => { navigate("/user/cases"); setMobileMenuOpen(false); }}>
              <List className="w-4 h-4 mr-2" />{t("myAnalyses")}
            </Button>
            <LanguageSwitcher className="w-full justify-start" />
            <Button variant="ghost" className="w-full justify-start" onClick={toggleTheme}>
              {theme === "light" ? <Moon className="w-4 h-4 mr-2" /> : <Sun className="w-4 h-4 mr-2" />}
              {theme === "light" ? t("darkMode") : t("lightMode")}
            </Button>
            <Button variant="ghost" className="w-full justify-start text-red-500" onClick={logout}>
              <LogOut className="w-4 h-4 mr-2" />{t("logout")}
            </Button>
          </div>
        )}
      </nav>
      <main className="max-w-7xl mx-auto p-4 sm:p-8">{children}</main>
    </div>
  );
};

// ==================== ADMIN DASHBOARD ====================

const AdminDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();
  const { t } = useLanguage();

  useEffect(() => { fetchAnalytics(); }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/admin/analytics`, { headers: { Authorization: `Bearer ${token}` } });
      setAnalytics(response.data);
    } catch (error) {
      console.error("Analytics yüklenemedi:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <AdminLayout><div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div></AdminLayout>;
  }

  return (
    <AdminLayout>
      <h1 className="text-2xl sm:text-3xl font-bold mb-6" data-testid="admin-dashboard-title">{t("dashboard")}</h1>
      
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <Card><CardHeader className="pb-2"><CardDescription>{t("totalUsers")}</CardDescription></CardHeader><CardContent><div className="text-3xl font-bold" data-testid="stat-total-users">{analytics?.users?.total || 0}</div><p className="text-xs text-green-600">{analytics?.users?.active || 0} {t("active")}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardDescription>{t("totalCases")}</CardDescription></CardHeader><CardContent><div className="text-3xl font-bold" data-testid="stat-total-cases">{analytics?.cases?.total || 0}</div><p className="text-xs text-gray-500">{analytics?.cases?.archived || 0} {t("archived")}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardDescription>{t("thisWeek")}</CardDescription></CardHeader><CardContent><div className="text-3xl font-bold text-primary">{analytics?.cases?.recent_week || 0}</div><p className="text-xs text-gray-500">{t("newAnalyses")}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardDescription>{t("totalEmailsSent")}</CardDescription></CardHeader><CardContent><div className="text-3xl font-bold text-blue-600" data-testid="stat-total-emails">{analytics?.total_emails_sent || 0}</div><p className="text-xs text-gray-500"><Mail className="w-3 h-3 inline mr-1" />e-posta</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardDescription>{t("warrantyCoverage")}</CardDescription></CardHeader><CardContent><div className="text-3xl font-bold text-green-600">{analytics?.decisions?.COVERED || 0}</div><p className="text-xs text-red-500">{analytics?.decisions?.OUT_OF_COVERAGE || 0} {t("outOfCoverage")}</p></CardContent></Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card><CardHeader><CardTitle className="text-lg">{t("branchDistribution")}</CardTitle></CardHeader><CardContent><div className="space-y-3">{analytics?.branches && Object.entries(analytics.branches).map(([branch, count]) => (<div key={branch} className="flex items-center justify-between"><span className="text-sm">{branch}</span><Badge variant="outline">{count}</Badge></div>))}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-lg">{t("warrantyDecisions")}</CardTitle></CardHeader><CardContent><div className="space-y-3"><div className="flex items-center justify-between"><span className="text-sm flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-500" />{t("covered")}</span><Badge className="bg-green-100 text-green-800">{analytics?.decisions?.COVERED || 0}</Badge></div><div className="flex items-center justify-between"><span className="text-sm flex items-center gap-2"><XCircle className="w-4 h-4 text-red-500" />{t("outOfCoverage")}</span><Badge className="bg-red-100 text-red-800">{analytics?.decisions?.OUT_OF_COVERAGE || 0}</Badge></div><div className="flex items-center justify-between"><span className="text-sm flex items-center gap-2"><AlertCircle className="w-4 h-4 text-yellow-500" />{t("additionalInfoRequired")}</span><Badge className="bg-yellow-100 text-yellow-800">{analytics?.decisions?.ADDITIONAL_INFO_REQUIRED || 0}</Badge></div></div></CardContent></Card>
      </div>
    </AdminLayout>
  );
};

// ==================== ADMIN USERS ====================

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ branch: "", role: "" });
  const { token } = useAuth();
  const { t } = useLanguage();

  useEffect(() => { fetchUsers(); }, [filter]);

  const fetchUsers = async () => {
    try {
      let url = `${API}/admin/users`;
      const params = new URLSearchParams();
      if (filter.branch) params.append("branch", filter.branch);
      if (filter.role) params.append("role", filter.role);
      if (params.toString()) url += `?${params.toString()}`;
      const response = await axios.get(url, { headers: { Authorization: `Bearer ${token}` } });
      setUsers(response.data);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleActive = async (userId) => { await axios.patch(`${API}/admin/users/${userId}/toggle-active`, {}, { headers: { Authorization: `Bearer ${token}` } }); fetchUsers(); };
  const addCredit = async (userId) => { await axios.patch(`${API}/admin/users/${userId}/add-credit?amount=5`, {}, { headers: { Authorization: `Bearer ${token}` } }); fetchUsers(); };
  const deleteUser = async (userId) => { if (!window.confirm(t("deleteUserConfirm"))) return; await axios.delete(`${API}/admin/users/${userId}`, { headers: { Authorization: `Bearer ${token}` } }); fetchUsers(); };

  // Toplam e-posta sayısı
  const totalEmails = users.reduce((sum, user) => sum + (user.emails_sent || 0), 0);

  return (
    <AdminLayout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold" data-testid="admin-users-title">{t("userManagement")}</h1>
          <p className="text-sm text-gray-500 mt-1">{t("totalEmailsSent")}: <span className="font-semibold text-primary">{totalEmails}</span></p>
        </div>
        <div className="flex gap-2">
          <Select value={filter.branch || "all"} onValueChange={(v) => setFilter({...filter, branch: v === "all" ? "" : v})}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder={t("allBranches")} /></SelectTrigger>
            <SelectContent><SelectItem value="all">{t("allBranches")}</SelectItem>{BRANCHES.map(b => <SelectItem key={b} value={b}>{b}</SelectItem>)}</SelectContent>
          </Select>
          <Select value={filter.role || "all"} onValueChange={(v) => setFilter({...filter, role: v === "all" ? "" : v})}>
            <SelectTrigger className="w-[120px]"><SelectValue placeholder={t("allRoles")} /></SelectTrigger>
            <SelectContent><SelectItem value="all">{t("allRoles")}</SelectItem><SelectItem value="admin">{t("admin")}</SelectItem><SelectItem value="user">{t("user")}</SelectItem></SelectContent>
          </Select>
        </div>
      </div>

      {loading ? <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div> : (
        <div className="space-y-4">
          {users.map(user => (
            <Card key={user.id} data-testid={`user-card-${user.id}`}>
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2"><span className="font-medium">{user.full_name}</span><Badge variant={user.role === "admin" ? "default" : "outline"}>{user.role}</Badge><Badge variant={user.is_active ? "default" : "destructive"}>{user.is_active ? t("active") : t("inactive")}</Badge></div>
                    <p className="text-sm text-gray-500">{user.email}</p>
                    <div className="flex gap-4 text-xs text-gray-500 flex-wrap">
                      {user.phone_number && <span><Phone className="w-3 h-3 inline mr-1" />{user.phone_number}</span>}
                      {user.branch && <span><Building className="w-3 h-3 inline mr-1" />{user.branch}</span>}
                      <span><CreditCard className="w-3 h-3 inline mr-1" />{t("credit")}: {user.free_analyses_remaining}</span>
                      <span><Mail className="w-3 h-3 inline mr-1" />{t("emailsSent")}: <span className="font-medium text-primary">{user.emails_sent || 0}</span></span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => addCredit(user.id)}><Plus className="w-4 h-4 mr-1" />5 {t("credit")}</Button>
                    <Button size="sm" variant="outline" onClick={() => toggleActive(user.id)}>{user.is_active ? t("makeInactive") : t("makeActive")}</Button>
                    <Button size="sm" variant="destructive" onClick={() => deleteUser(user.id)}><Trash2 className="w-4 h-4" /></Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {users.length === 0 && <Card><CardContent className="p-8 text-center text-gray-500">{t("noUsers")}</CardContent></Card>}
        </div>
      )}
    </AdminLayout>
  );
};

// ==================== ADMIN ALL CASES ====================

const AdminAllCases = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ branch: "", archived: "" });
  const { token } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  useEffect(() => { fetchCases(); }, [filter]);

  const fetchCases = async () => {
    try {
      let url = `${API}/admin/cases`;
      const params = new URLSearchParams();
      if (filter.branch) params.append("branch", filter.branch);
      if (filter.archived !== "") params.append("archived", filter.archived);
      if (params.toString()) url += `?${params.toString()}`;
      const response = await axios.get(url, { headers: { Authorization: `Bearer ${token}` } });
      setCases(response.data);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const archiveCase = async (caseId) => { await axios.patch(`${API}/admin/cases/${caseId}/archive`, {}, { headers: { Authorization: `Bearer ${token}` } }); fetchCases(); };
  const deleteCase = async (caseId) => { if (!window.confirm(t("deleteCaseConfirm"))) return; await axios.delete(`${API}/admin/cases/${caseId}`, { headers: { Authorization: `Bearer ${token}` } }); fetchCases(); };

  const getDecisionBadge = (decision) => {
    const colors = { "COVERED": "bg-green-100 text-green-800", "OUT_OF_COVERAGE": "bg-red-100 text-red-800", "ADDITIONAL_INFO_REQUIRED": "bg-yellow-100 text-yellow-800" };
    return colors[decision] || "bg-gray-100 text-gray-800";
  };

  return (
    <AdminLayout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold" data-testid="admin-cases-title">{t("allIzeCases")}</h1>
        <div className="flex gap-2">
          <Select value={filter.branch || "all"} onValueChange={(v) => setFilter({...filter, branch: v === "all" ? "" : v})}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder={t("allBranches")} /></SelectTrigger>
            <SelectContent><SelectItem value="all">{t("allBranches")}</SelectItem>{BRANCHES.map(b => <SelectItem key={b} value={b}>{b}</SelectItem>)}</SelectContent>
          </Select>
          <Select value={filter.archived || "all"} onValueChange={(v) => setFilter({...filter, archived: v === "all" ? "" : v})}>
            <SelectTrigger className="w-[120px]"><SelectValue placeholder={t("all")} /></SelectTrigger>
            <SelectContent><SelectItem value="all">{t("all")}</SelectItem><SelectItem value="false">{t("active")}</SelectItem><SelectItem value="true">{t("archive")}</SelectItem></SelectContent>
          </Select>
        </div>
      </div>

      {loading ? <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div> : (
        <div className="space-y-4">
          {cases.map(c => (
            <Card key={c.id} className={c.is_archived ? "opacity-60" : ""} data-testid={`case-card-${c.id}`}>
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap"><span className="font-medium">{c.ize_no}</span><Badge className={getDecisionBadge(c.warranty_decision)}>{c.warranty_decision}</Badge>{c.is_archived && <Badge variant="secondary"><Archive className="w-3 h-3 mr-1" />{t("archived")}</Badge>}</div>
                    <p className="text-sm text-gray-500">{c.company} - {c.case_title}</p>
                    <div className="flex gap-4 text-xs text-gray-500">{c.branch && <span><Building className="w-3 h-3 inline mr-1" />{c.branch}</span>}<span>{new Date(c.created_at).toLocaleDateString('tr-TR')}</span></div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => navigate(`/case/${c.id}`)}><Eye className="w-4 h-4 mr-1" />{t("view")}</Button>
                    <Button size="sm" variant="outline" onClick={() => archiveCase(c.id)}><Archive className="w-4 h-4 mr-1" />{c.is_archived ? t("unarchiveCase") : t("archiveCase")}</Button>
                    <Button size="sm" variant="destructive" onClick={() => deleteCase(c.id)}><Trash2 className="w-4 h-4" /></Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {cases.length === 0 && <Card><CardContent className="p-8 text-center text-gray-500">{t("noCases")}</CardContent></Card>}
        </div>
      )}
    </AdminLayout>
  );
};

// ==================== ADMIN RULES ====================

const AdminRules = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showManualForm, setShowManualForm] = useState(false);
  const [showPdfUpload, setShowPdfUpload] = useState(false);
  const [formData, setFormData] = useState({ rule_version: "", rule_text: "", keywords: "" });
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfVersion, setPdfVersion] = useState("");
  const [pdfKeywords, setPdfKeywords] = useState("");
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const { token } = useAuth();
  const { t } = useLanguage();

  useEffect(() => { fetchRules(); }, []);

  const fetchRules = async () => {
    try { 
      const response = await axios.get(`${API}/warranty-rules`, { headers: { Authorization: `Bearer ${token}` } }); 
      setRules(response.data); 
    } catch (error) { 
      console.error("Error:", error); 
    } finally { 
      setLoading(false); 
    }
  };

  const createRule = async (e) => {
    e.preventDefault();
    await axios.post(`${API}/warranty-rules`, { 
      rule_version: formData.rule_version, 
      rule_text: formData.rule_text, 
      keywords: formData.keywords.split(",").map(k => k.trim()).filter(k => k) 
    }, { headers: { Authorization: `Bearer ${token}` } });
    setShowManualForm(false); 
    setFormData({ rule_version: "", rule_text: "", keywords: "" }); 
    fetchRules();
  };

  const uploadPdf = async (e) => {
    e.preventDefault();
    if (!pdfFile || !pdfVersion) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", pdfFile);
      formData.append("rule_version", pdfVersion);
      formData.append("keywords", pdfKeywords);
      
      await axios.post(`${API}/warranty-rules/upload-pdf`, formData, { 
        headers: { 
          Authorization: `Bearer ${token}`, 
          "Content-Type": "multipart/form-data" 
        } 
      });
      
      setShowPdfUpload(false);
      setPdfFile(null);
      setPdfVersion("");
      setPdfKeywords("");
      fetchRules();
      alert(t("ruleUploaded"));
    } catch (error) {
      alert(t("error") + ": " + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  const toggleActive = async (ruleId) => { 
    await axios.patch(`${API}/warranty-rules/${ruleId}/toggle-active`, {}, { headers: { Authorization: `Bearer ${token}` } }); 
    fetchRules(); 
  };

  const deleteRule = async (ruleId) => { 
    if (!window.confirm(t("delete") + "?")) return; 
    await axios.delete(`${API}/warranty-rules/${ruleId}`, { headers: { Authorization: `Bearer ${token}` } }); 
    fetchRules(); 
  };

  const filteredRules = activeTab === "active" ? rules.filter(r => r.is_active) : rules;

  return (
    <AdminLayout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold" data-testid="admin-rules-title">{t("warrantyRules")}</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => { setShowPdfUpload(true); setShowManualForm(false); }}>
            <Upload className="w-4 h-4 mr-2" />{t("uploadPdf")}
          </Button>
          <Button onClick={() => { setShowManualForm(true); setShowPdfUpload(false); }}>
            <Plus className="w-4 h-4 mr-2" />{t("addManually")}
          </Button>
        </div>
      </div>

      {/* PDF Upload Form */}
      {showPdfUpload && (
        <Card className="mb-6 border-primary/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-primary" />
              {t("uploadWarrantyPdf")}
            </CardTitle>
            <CardDescription>{t("uploadWarrantyPdfDesc")}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={uploadPdf} className="space-y-4">
              <div>
                <Label>{t("ruleVersion")} *</Label>
                <Input 
                  value={pdfVersion} 
                  onChange={(e) => setPdfVersion(e.target.value)} 
                  required 
                  placeholder="2.0" 
                />
              </div>
              <div>
                <Label>{t("selectPdfFile")} *</Label>
                <Input 
                  type="file" 
                  accept=".pdf" 
                  onChange={(e) => setPdfFile(e.target.files[0])} 
                  required 
                  className="cursor-pointer"
                />
                {pdfFile && (
                  <p className="text-sm text-green-600 mt-1">
                    <FileText className="w-4 h-4 inline mr-1" />
                    {pdfFile.name}
                  </p>
                )}
              </div>
              <div>
                <Label>{t("metaKeywords")}</Label>
                <Input 
                  value={pdfKeywords} 
                  onChange={(e) => setPdfKeywords(e.target.value)} 
                  placeholder={t("metaKeywordsHelp")} 
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={uploading}>
                  {uploading ? t("loading") : t("uploadPdf")}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowPdfUpload(false)}>
                  {t("cancel")}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Manual Form */}
      {showManualForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{t("addManually")}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={createRule} className="space-y-4">
              <div>
                <Label>{t("ruleVersion")} *</Label>
                <Input 
                  value={formData.rule_version} 
                  onChange={(e) => setFormData({...formData, rule_version: e.target.value})} 
                  required 
                  placeholder="1.0" 
                />
              </div>
              <div>
                <Label>{t("ruleText")} *</Label>
                <Textarea 
                  className="min-h-[150px]" 
                  value={formData.rule_text} 
                  onChange={(e) => setFormData({...formData, rule_text: e.target.value})} 
                  required 
                  placeholder="Garanti kuralları metni..."
                />
              </div>
              <div>
                <Label>{t("metaKeywords")}</Label>
                <Input 
                  value={formData.keywords} 
                  onChange={(e) => setFormData({...formData, keywords: e.target.value})} 
                  placeholder={t("metaKeywordsHelp")} 
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit">{t("save")}</Button>
                <Button type="button" variant="outline" onClick={() => setShowManualForm(false)}>
                  {t("cancel")}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-4">
        <TabsList>
          <TabsTrigger value="all">{t("allRulesTab")} ({rules.length})</TabsTrigger>
          <TabsTrigger value="active">{t("activeRules")} ({rules.filter(r => r.is_active).length})</TabsTrigger>
        </TabsList>
      </Tabs>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredRules.map(rule => (
            <Card key={rule.id} className={!rule.is_active ? "opacity-60" : ""}>
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge>v{rule.rule_version}</Badge>
                      <Badge variant={rule.source_type === "pdf" ? "secondary" : "outline"}>
                        {rule.source_type === "pdf" ? (
                          <><FileText className="w-3 h-3 mr-1" />{t("pdf")}</>
                        ) : (
                          <><Edit className="w-3 h-3 mr-1" />{t("manual")}</>
                        )}
                      </Badge>
                      <Badge variant={rule.is_active ? "default" : "destructive"}>
                        {rule.is_active ? t("active") : t("inactive")}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(rule.created_at).toLocaleDateString('tr-TR')}
                      </span>
                    </div>
                    {rule.source_filename && (
                      <p className="text-xs text-gray-500">
                        <FileText className="w-3 h-3 inline mr-1" />
                        {rule.source_filename}
                      </p>
                    )}
                    <p className="text-sm line-clamp-3">{rule.rule_text}</p>
                    {rule.keywords?.length > 0 && (
                      <div className="flex gap-1 flex-wrap">
                        {rule.keywords.map((k, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{k}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => toggleActive(rule.id)}
                      title={t("toggleActiveStatus")}
                    >
                      {rule.is_active ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => deleteRule(rule.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {filteredRules.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center text-gray-500">{t("noRules")}</CardContent>
            </Card>
          )}
        </div>
      )}
    </AdminLayout>
  );
};

// ==================== ADMIN API SETTINGS ====================

const AdminAPISettings = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({ emergent_key: "", openai_key: "", anthropic_key: "", google_key: "" });
  const [showKeys, setShowKeys] = useState({});
  const { token } = useAuth();
  const { t } = useLanguage();

  useEffect(() => { fetchSettings(); }, []);

  const fetchSettings = async () => { try { const response = await axios.get(`${API}/admin/settings`, { headers: { Authorization: `Bearer ${token}` } }); setSettings(response.data); } catch (error) { console.error("Error:", error); } finally { setLoading(false); } };

  const updateSettings = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const updateData = {};
      if (formData.emergent_key) updateData.emergent_key = formData.emergent_key;
      if (formData.openai_key) updateData.openai_key = formData.openai_key;
      if (formData.anthropic_key) updateData.anthropic_key = formData.anthropic_key;
      if (formData.google_key) updateData.google_key = formData.google_key;
      await axios.put(`${API}/admin/settings`, updateData, { headers: { Authorization: `Bearer ${token}` } });
      setFormData({ emergent_key: "", openai_key: "", anthropic_key: "", google_key: "" }); fetchSettings(); alert(t("settingsSaved"));
    } catch (error) { alert(t("error") + ": " + error.message); } finally { setSaving(false); }
  };

  if (loading) return <AdminLayout><div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div></AdminLayout>;

  return (
    <AdminLayout>
      <h1 className="text-2xl sm:text-3xl font-bold mb-6" data-testid="admin-settings-title">{t("apiSettings")}</h1>
      <div className="grid gap-6">
        <Card><CardHeader><CardTitle>{t("currentApiKeys")}</CardTitle><CardDescription>{t("maskedKeys")}</CardDescription></CardHeader><CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-primary/5 rounded-lg"><div><Label className="text-primary font-semibold">{t("emergentKeyRecommended")}</Label><p className="text-sm text-gray-500 font-mono">{settings?.emergent_key_masked || t("notSet")}</p><p className="text-xs text-gray-400 mt-1">{t("emergentKeyDesc")}</p></div><Badge variant={settings?.emergent_key ? "default" : "outline"}>{settings?.emergent_key ? t("active") : t("notSet")}</Badge></div>
          <Separator />
          <div className="flex items-center justify-between"><div><Label>OpenAI API Key</Label><p className="text-sm text-gray-500 font-mono">{settings?.openai_key_masked || t("notSet")}</p></div><Badge variant={settings?.openai_key ? "default" : "outline"}>{settings?.openai_key ? t("active") : t("notSet")}</Badge></div>
          <Separator />
          <div className="flex items-center justify-between"><div><Label>Anthropic API Key</Label><p className="text-sm text-gray-500 font-mono">{settings?.anthropic_key_masked || t("notSet")}</p></div><Badge variant={settings?.anthropic_key ? "default" : "outline"}>{settings?.anthropic_key ? t("active") : t("notSet")}</Badge></div>
          <Separator />
          <div className="flex items-center justify-between"><div><Label>Google API Key</Label><p className="text-sm text-gray-500 font-mono">{settings?.google_key_masked || t("notSet")}</p></div><Badge variant={settings?.google_key ? "default" : "outline"}>{settings?.google_key ? t("active") : t("notSet")}</Badge></div>
        </CardContent></Card>

        <Card><CardHeader><CardTitle>{t("updateApiKeys")}</CardTitle><CardDescription>{t("enterNewKey")}</CardDescription></CardHeader><CardContent>
          <form onSubmit={updateSettings} className="space-y-4">
            <div className="p-4 border-2 border-primary/20 rounded-lg bg-primary/5">
              <Label className="text-primary font-semibold">{t("emergentKeyRecommended")}</Label>
              <p className="text-xs text-gray-500 mb-2">{t("emergentKeyDesc")}</p>
              <div className="relative"><Input type={showKeys.emergent ? "text" : "password"} value={formData.emergent_key} onChange={(e) => setFormData({...formData, emergent_key: e.target.value})} placeholder="sk-emergent-..." /><Button type="button" variant="ghost" size="sm" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowKeys({...showKeys, emergent: !showKeys.emergent})}>{showKeys.emergent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}</Button></div>
            </div>
            <Separator />
            <div><Label>OpenAI API Key</Label><div className="relative"><Input type={showKeys.openai ? "text" : "password"} value={formData.openai_key} onChange={(e) => setFormData({...formData, openai_key: e.target.value})} placeholder="sk-..." /><Button type="button" variant="ghost" size="sm" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowKeys({...showKeys, openai: !showKeys.openai})}>{showKeys.openai ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}</Button></div></div>
            <div><Label>Anthropic API Key</Label><div className="relative"><Input type={showKeys.anthropic ? "text" : "password"} value={formData.anthropic_key} onChange={(e) => setFormData({...formData, anthropic_key: e.target.value})} placeholder="sk-ant-..." /><Button type="button" variant="ghost" size="sm" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowKeys({...showKeys, anthropic: !showKeys.anthropic})}>{showKeys.anthropic ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}</Button></div></div>
            <div><Label>Google API Key</Label><div className="relative"><Input type={showKeys.google ? "text" : "password"} value={formData.google_key} onChange={(e) => setFormData({...formData, google_key: e.target.value})} placeholder="AIza..." /><Button type="button" variant="ghost" size="sm" className="absolute right-0 top-0 h-full px-3" onClick={() => setShowKeys({...showKeys, google: !showKeys.google})}>{showKeys.google ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}</Button></div></div>
            <Button type="submit" disabled={saving}>{saving ? t("loading") : t("save")}</Button>
          </form>
        </CardContent></Card>
      </div>
    </AdminLayout>
  );
};

// ==================== ADMIN EMAIL SETTINGS ====================

const AdminEmailSettings = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { token } = useAuth();
  const { t } = useLanguage();

  useEffect(() => { fetchSettings(); }, []);

  const fetchSettings = async () => {
    try { 
      const response = await axios.get(`${API}/admin/email-settings`, { headers: { Authorization: `Bearer ${token}` } }); 
      setSettings(response.data); 
    } 
    catch (error) { console.error("Error:", error); } 
    finally { setLoading(false); }
  };

  const handleChange = (field, value) => {
    setSettings({ ...settings, [field]: value });
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const updateData = {};
      if (settings.smtp_host) updateData.smtp_host = settings.smtp_host;
      if (settings.smtp_port) updateData.smtp_port = settings.smtp_port;
      if (settings.smtp_user) updateData.smtp_user = settings.smtp_user;
      if (settings.smtp_password) updateData.smtp_password = settings.smtp_password;
      if (settings.sender_name) updateData.sender_name = settings.sender_name;
      if (settings.sender_email) updateData.sender_email = settings.sender_email;
      updateData.email_enabled = settings.email_enabled;
      
      await axios.put(`${API}/admin/email-settings`, updateData, { headers: { Authorization: `Bearer ${token}` } });
      fetchSettings();
      alert(t("settingsSaved"));
    } catch (error) {
      alert(t("error") + ": " + error.message);
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      const response = await axios.post(`${API}/admin/email-settings/test`, {}, { headers: { Authorization: `Bearer ${token}` } });
      if (response.data.success) {
        alert(t("testConnectionSuccess"));
      } else {
        alert(t("testConnectionFailed") + ": " + response.data.message);
      }
    } catch (error) {
      alert(t("testConnectionFailed") + ": " + (error.response?.data?.message || error.message));
    } finally {
      setTesting(false);
    }
  };

  if (loading) return <AdminLayout><div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div></AdminLayout>;

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold" data-testid="admin-email-settings-title">{t("emailSettings")}</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={testConnection} disabled={testing}>
            {testing ? t("loading") : t("testConnection")}
          </Button>
          <Button onClick={saveSettings} disabled={saving}>{saving ? t("loading") : t("save")}</Button>
        </div>
      </div>

      <div className="grid gap-6">
        {/* SMTP Ayarları */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-primary" />
              {t("smtpSettings")}
            </CardTitle>
            <CardDescription>{t("emailSettingsDesc")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label>{t("smtpHost")}</Label>
                <Input 
                  value={settings?.smtp_host || ""} 
                  onChange={(e) => handleChange("smtp_host", e.target.value)} 
                  placeholder="smtp.visupanel.com" 
                />
              </div>
              <div>
                <Label>{t("smtpPort")}</Label>
                <Input 
                  type="number"
                  value={settings?.smtp_port || 587} 
                  onChange={(e) => handleChange("smtp_port", parseInt(e.target.value))} 
                  placeholder="587" 
                />
              </div>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label>{t("smtpUser")}</Label>
                <Input 
                  value={settings?.smtp_user || ""} 
                  onChange={(e) => handleChange("smtp_user", e.target.value)} 
                  placeholder="info@visupanel.com" 
                />
              </div>
              <div>
                <Label>{t("smtpPassword")}</Label>
                <div className="relative">
                  <Input 
                    type={showPassword ? "text" : "password"}
                    value={settings?.smtp_password || ""} 
                    onChange={(e) => handleChange("smtp_password", e.target.value)} 
                    placeholder="********" 
                  />
                  <Button 
                    type="button" 
                    variant="ghost" 
                    size="sm" 
                    className="absolute right-0 top-0 h-full px-3" 
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </Button>
                </div>
                {settings?.smtp_password_masked && !settings?.smtp_password && (
                  <p className="text-xs text-gray-500 mt-1">Mevcut: {settings.smtp_password_masked}</p>
                )}
              </div>
            </div>
            <Separator />
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label>{t("senderName")}</Label>
                <Input 
                  value={settings?.sender_name || ""} 
                  onChange={(e) => handleChange("sender_name", e.target.value)} 
                  placeholder="IZE Case Resolver" 
                />
              </div>
              <div>
                <Label>{t("senderEmail")}</Label>
                <Input 
                  type="email"
                  value={settings?.sender_email || ""} 
                  onChange={(e) => handleChange("sender_email", e.target.value)} 
                  placeholder="info@visupanel.com" 
                />
              </div>
            </div>
            <Separator />
            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div>
                <Label className="text-base">{t("emailEnabled")}</Label>
                <p className="text-sm text-gray-500">Analiz tamamlandığında kullanıcıya e-posta gönderilsin</p>
              </div>
              <Button 
                variant={settings?.email_enabled ? "default" : "outline"}
                onClick={() => handleChange("email_enabled", !settings?.email_enabled)}
              >
                {settings?.email_enabled ? t("active") : t("inactive")}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
};

// ==================== ADMIN SITE SETTINGS ====================

const AdminSiteSettings = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { token } = useAuth();
  const { t, fetchSiteSettings: refreshSiteSettings } = useLanguage();

  useEffect(() => { fetchSettings(); }, []);

  const fetchSettings = async () => {
    try { const response = await axios.get(`${API}/site-settings`, { headers: { Authorization: `Bearer ${token}` } }); setSettings(response.data); } 
    catch (error) { console.error("Error:", error); } 
    finally { setLoading(false); }
  };

  const handleChange = (field, value) => {
    setSettings({ ...settings, [field]: value });
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/site-settings`, settings, { headers: { Authorization: `Bearer ${token}` } });
      refreshSiteSettings();
      alert(t("settingsSaved"));
    } catch (error) {
      alert(t("error") + ": " + error.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <AdminLayout><div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div></AdminLayout>;

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold" data-testid="admin-site-settings-title">{t("siteSettingsTitle")}</h1>
        <Button onClick={saveSettings} disabled={saving}>{saving ? t("loading") : t("save")}</Button>
      </div>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="general">{t("generalSettings")}</TabsTrigger>
          <TabsTrigger value="seo">{t("seoSettings")}</TabsTrigger>
          <TabsTrigger value="analytics">{t("analyticsSettings")}</TabsTrigger>
          <TabsTrigger value="contact">{t("contactSettings")}</TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <Card>
            <CardHeader><CardTitle>{t("generalSettings")}</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div><Label>{t("siteName")}</Label><Input value={settings?.site_name || ""} onChange={(e) => handleChange("site_name", e.target.value)} placeholder="IZE Case Resolver" /></div>
              <div><Label>{t("siteTitle")}</Label><Input value={settings?.site_title || ""} onChange={(e) => handleChange("site_title", e.target.value)} placeholder="IZE Case Resolver - AI ile Garanti Analizi" /></div>
              <div><Label>{t("siteDescription")}</Label><Textarea value={settings?.site_description || ""} onChange={(e) => handleChange("site_description", e.target.value)} placeholder="Site açıklaması..." rows={3} /></div>
              <div>
                <Label>{t("defaultLanguage")}</Label>
                <Select value={settings?.default_language || "tr"} onValueChange={(v) => handleChange("default_language", v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="tr">{t("turkish")}</SelectItem>
                    <SelectItem value="en">{t("english")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div><Label>{t("footerText")}</Label><Input value={settings?.footer_text || ""} onChange={(e) => handleChange("footer_text", e.target.value)} placeholder="© 2026 ..." /></div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="seo">
          <Card>
            <CardHeader><CardTitle>{t("seoSettings")}</CardTitle><CardDescription>Google arama sonuçlarında görünecek bilgiler</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <div><Label>{t("metaTitle")}</Label><Input value={settings?.meta_title || ""} onChange={(e) => handleChange("meta_title", e.target.value)} placeholder="Sayfa Başlığı - Marka" /><p className="text-xs text-gray-500 mt-1">Google'da görünecek başlık (50-60 karakter önerilir)</p></div>
              <div><Label>{t("metaDescription")}</Label><Textarea value={settings?.meta_description || ""} onChange={(e) => handleChange("meta_description", e.target.value)} placeholder="Site açıklaması..." rows={3} /><p className="text-xs text-gray-500 mt-1">Google'da görünecek açıklama (150-160 karakter önerilir)</p></div>
              <div><Label>{t("metaKeywords")}</Label><Input value={settings?.meta_keywords || ""} onChange={(e) => handleChange("meta_keywords", e.target.value)} placeholder="ize, garanti, warranty, renault, analiz" /><p className="text-xs text-gray-500 mt-1">{t("metaKeywordsHelp")}</p></div>
              <div><Label>OG Image URL</Label><Input value={settings?.og_image_url || ""} onChange={(e) => handleChange("og_image_url", e.target.value)} placeholder="https://example.com/og-image.jpg" /><p className="text-xs text-gray-500 mt-1">Sosyal medyada paylaşıldığında görünecek resim</p></div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <Card>
            <CardHeader><CardTitle>{t("analyticsSettings")}</CardTitle><CardDescription>Site trafiğini takip etmek için analytics kodları</CardDescription></CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <Label className="text-blue-700 dark:text-blue-300">{t("googleAnalyticsId")}</Label>
                <Input className="mt-2" value={settings?.google_analytics_id || ""} onChange={(e) => handleChange("google_analytics_id", e.target.value)} placeholder="G-XXXXXXXXXX" />
                <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">{t("googleAnalyticsHelp")}</p>
              </div>
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <Label className="text-green-700 dark:text-green-300">{t("googleTagManagerId")}</Label>
                <Input className="mt-2" value={settings?.google_tag_manager_id || ""} onChange={(e) => handleChange("google_tag_manager_id", e.target.value)} placeholder="GTM-XXXXXXX" />
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">{t("googleTagManagerHelp")}</p>
              </div>
              <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                <Label className="text-orange-700 dark:text-orange-300">{t("yandexMetricaId")}</Label>
                <Input className="mt-2" value={settings?.yandex_metrica_id || ""} onChange={(e) => handleChange("yandex_metrica_id", e.target.value)} placeholder="XXXXXXXX" />
                <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">{t("yandexMetricaHelp")}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="contact">
          <Card>
            <CardHeader><CardTitle>{t("contactSettings")}</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div><Label>{t("companyName")}</Label><Input value={settings?.company_name || ""} onChange={(e) => handleChange("company_name", e.target.value)} placeholder="Şirket Adı" /></div>
              <div><Label>{t("contactEmail")}</Label><Input type="email" value={settings?.contact_email || ""} onChange={(e) => handleChange("contact_email", e.target.value)} placeholder="info@example.com" /></div>
              <div><Label>{t("contactPhone")}</Label><Input value={settings?.contact_phone || ""} onChange={(e) => handleChange("contact_phone", e.target.value)} placeholder="+90 XXX XXX XX XX" /></div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </AdminLayout>
  );
};

// ==================== USER UPLOAD ====================

const UserUpload = () => {
  const [file, setFile] = useState(null);
  const [branch, setBranch] = useState("");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const { token, user, fetchUser } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true); setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (branch) formData.append("branch", branch);
      const response = await axios.post(`${API}/cases/analyze`, formData, { headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" } });
      fetchUser();
      navigate(`/case/${response.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || t("error"));
    } finally {
      setUploading(false);
    }
  };

  return (
    <UserLayout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl sm:text-3xl font-bold mb-6" data-testid="user-upload-title">{t("uploadTitle")}</h1>
        {user?.free_analyses_remaining <= 0 && (<Alert variant="destructive" className="mb-6"><AlertCircle className="h-4 w-4" /><AlertDescription>{t("noCredits")}</AlertDescription></Alert>)}
        <Card><CardContent className="p-6">
          <form onSubmit={handleUpload} className="space-y-6">
            <div>
              <Label>PDF</Label>
              <div className={`mt-2 border-2 border-dashed rounded-lg p-8 text-center ${file ? 'border-primary bg-primary/5' : 'border-gray-300'}`}>
                <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} className="hidden" id="pdf-upload" data-testid="file-input" />
                <label htmlFor="pdf-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  {file ? <p className="text-primary font-medium">{file.name}</p> : (<><p className="text-gray-600">{t("selectFile")}</p><p className="text-sm text-gray-400 mt-1">{t("maxFileSize")}</p></>)}
                </label>
              </div>
            </div>
            <div>
              <Label>{t("branch")}</Label>
              <Select value={branch} onValueChange={setBranch}>
                <SelectTrigger data-testid="upload-branch"><SelectValue placeholder={t("branch")} /></SelectTrigger>
                <SelectContent>{BRANCHES.map(b => (<SelectItem key={b} value={b}>{b}</SelectItem>))}</SelectContent>
              </Select>
            </div>
            {error && (<Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>)}
            <Button type="submit" className="w-full" disabled={!file || uploading || user?.free_analyses_remaining <= 0} data-testid="upload-submit">
              {uploading ? (<><div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>{t("analyzing")}</>) : (<><Upload className="w-4 h-4 mr-2" />{t("analyze")}</>)}
            </Button>
          </form>
        </CardContent></Card>
      </div>
    </UserLayout>
  );
};

// ==================== USER CASES ====================

const UserCases = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  useEffect(() => { fetchCases(); }, []);

  const fetchCases = async () => {
    try { const response = await axios.get(`${API}/cases`, { headers: { Authorization: `Bearer ${token}` } }); setCases(response.data); } catch (error) { console.error("Error:", error); } finally { setLoading(false); }
  };

  const getDecisionBadge = (decision) => {
    const colors = { "COVERED": "bg-green-100 text-green-800", "OUT_OF_COVERAGE": "bg-red-100 text-red-800", "ADDITIONAL_INFO_REQUIRED": "bg-yellow-100 text-yellow-800" };
    const labels = { "COVERED": t("covered"), "OUT_OF_COVERAGE": t("outOfCoverage"), "ADDITIONAL_INFO_REQUIRED": t("additionalInfoRequired") };
    return { color: colors[decision] || "bg-gray-100 text-gray-800", label: labels[decision] || decision };
  };

  return (
    <UserLayout>
      <h1 className="text-2xl sm:text-3xl font-bold mb-6" data-testid="user-cases-title">{t("myAnalyses")}</h1>
      {loading ? <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div> : (
        <div className="space-y-4">
          {cases.map(c => {
            const badge = getDecisionBadge(c.warranty_decision);
            return (
              <Card key={c.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate(`/case/${c.id}`)} data-testid={`case-item-${c.id}`}>
                <CardContent className="p-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2"><span className="font-medium">{c.ize_no}</span><Badge className={badge.color}>{badge.label}</Badge></div>
                      <p className="text-sm text-gray-500">{c.company}</p>
                    </div>
                    <span className="text-xs text-gray-400">{new Date(c.created_at).toLocaleDateString('tr-TR')}</span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
          {cases.length === 0 && (
            <Card><CardContent className="p-8 text-center">
              <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">{t("noAnalyses")}</p>
              <Button className="mt-4" onClick={() => navigate("/user/upload")}>{t("firstAnalysis")}</Button>
            </CardContent></Card>
          )}
        </div>
      )}
    </UserLayout>
  );
};

// ==================== CASE DETAIL ====================

const CaseDetail = () => {
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedSections, setExpandedSections] = useState({ vehicle: true, warranty: true, operations: false, email: false });
  const { token, user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const caseId = window.location.pathname.split('/').pop();

  useEffect(() => { fetchCase(); }, [caseId]);

  const fetchCase = async () => {
    try { const response = await axios.get(`${API}/cases/${caseId}`, { headers: { Authorization: `Bearer ${token}` } }); setCaseData(response.data); } catch (error) { navigate("/dashboard"); } finally { setLoading(false); }
  };

  const toggleSection = (section) => { setExpandedSections(prev => ({...prev, [section]: !prev[section]})); };

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div>;
  if (!caseData) return null;

  const Layout = user?.role === "admin" ? AdminLayout : UserLayout;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <Button variant="ghost" className="mb-4" onClick={() => navigate(-1)}>&larr; {t("back")}</Button>
        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold" data-testid="case-detail-title">{caseData.case_title}</h1>
          <p className="text-gray-500">IZE No: {caseData.ize_no}</p>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader className="cursor-pointer" onClick={() => toggleSection('vehicle')}>
              <div className="flex items-center justify-between"><CardTitle className="text-lg">{t("vehicleInfo")}</CardTitle>{expandedSections.vehicle ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}</div>
            </CardHeader>
            {expandedSections.vehicle && (
              <CardContent className="space-y-2">
                <div className="grid grid-cols-2 gap-4">
                  <div><span className="text-gray-500">{t("company")}:</span> {caseData.company}</div>
                  <div><span className="text-gray-500">{t("plate")}:</span> {caseData.plate}</div>
                  <div><span className="text-gray-500">{t("vin")}:</span> {caseData.vin}</div>
                  <div><span className="text-gray-500">{t("km")}:</span> {caseData.repair_km?.toLocaleString()}</div>
                  <div><span className="text-gray-500">{t("warrantyStart")}:</span> {caseData.warranty_start_date}</div>
                  <div><span className="text-gray-500">{t("repairDate")}:</span> {caseData.repair_date}</div>
                  <div><span className="text-gray-500">{t("vehicleAge")}:</span> {caseData.vehicle_age_months} {t("months")}</div>
                  {caseData.branch && <div><span className="text-gray-500">{t("branch")}:</span> {caseData.branch}</div>}
                </div>
              </CardContent>
            )}
          </Card>

          <Card>
            <CardHeader className="cursor-pointer" onClick={() => toggleSection('warranty')}>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  {t("warrantyEvaluation")}
                  <Badge className={caseData.warranty_decision === "COVERED" ? "bg-green-100 text-green-800" : caseData.warranty_decision === "OUT_OF_COVERAGE" ? "bg-red-100 text-red-800" : "bg-yellow-100 text-yellow-800"}>{caseData.warranty_decision}</Badge>
                </CardTitle>
                {expandedSections.warranty ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </div>
            </CardHeader>
            {expandedSections.warranty && (
              <CardContent className="space-y-4">
                <div><span className="text-gray-500">{t("withinWarranty")}:</span> {caseData.is_within_2_year_warranty ? <Badge className="bg-green-100 text-green-800">{t("yes")}</Badge> : <Badge className="bg-red-100 text-red-800">{t("no")}</Badge>}</div>
                {caseData.decision_rationale?.length > 0 && (<div><span className="text-gray-500 block mb-2">{t("decisionRationale")}:</span><ul className="list-disc list-inside space-y-1">{caseData.decision_rationale.map((r, i) => (<li key={i} className="text-sm">{r}</li>))}</ul></div>)}
                <div><span className="text-gray-500">{t("failureComplaint")}:</span><p className="text-sm mt-1">{caseData.failure_complaint || "-"}</p></div>
                <div><span className="text-gray-500">{t("failureCause")}:</span><p className="text-sm mt-1">{caseData.failure_cause || "-"}</p></div>
              </CardContent>
            )}
          </Card>

          <Card>
            <CardHeader className="cursor-pointer" onClick={() => toggleSection('operations')}>
              <div className="flex items-center justify-between"><CardTitle className="text-lg">{t("operationsAndParts")}</CardTitle>{expandedSections.operations ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}</div>
            </CardHeader>
            {expandedSections.operations && (
              <CardContent className="space-y-4">
                {caseData.operations_performed?.length > 0 && (<div><span className="text-gray-500 block mb-2">{t("operations")}:</span><ul className="list-disc list-inside space-y-1">{caseData.operations_performed.map((op, i) => (<li key={i} className="text-sm">{op}</li>))}</ul></div>)}
                {caseData.parts_replaced?.length > 0 && (<div><span className="text-gray-500 block mb-2">{t("replacedParts")}:</span><div className="space-y-2">{caseData.parts_replaced.map((part, i) => (<div key={i} className="bg-gray-50 dark:bg-gray-800 p-2 rounded text-sm"><strong>{part.partName}</strong> x{part.qty}{part.description && <p className="text-gray-500 text-xs">{part.description}</p>}</div>))}</div></div>)}
                <div><span className="text-gray-500">{t("repairSummary")}:</span><p className="text-sm mt-1">{caseData.repair_process_summary || "-"}</p></div>
              </CardContent>
            )}
          </Card>

          <Card>
            <CardHeader className="cursor-pointer" onClick={() => toggleSection('email')}>
              <div className="flex items-center justify-between"><CardTitle className="text-lg">{t("emailDraft")}</CardTitle>{expandedSections.email ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}</div>
            </CardHeader>
            {expandedSections.email && (
              <CardContent className="space-y-4">
                <div><span className="text-gray-500">{t("subject")}:</span><p className="text-sm mt-1 font-medium">{caseData.email_subject}</p></div>
                <div><span className="text-gray-500">{t("content")}:</span><div className="mt-2 bg-gray-50 dark:bg-gray-800 p-4 rounded whitespace-pre-wrap text-sm">{caseData.email_body}</div></div>
                <Button variant="outline" onClick={() => navigator.clipboard.writeText(caseData.email_body)}>{t("copyEmail")}</Button>
              </CardContent>
            )}
          </Card>
        </div>
      </div>
    </Layout>
  );
};

// ==================== PAYMENT WRAPPERS ====================

const PaymentPageWrapper = () => {
  const { user, token } = useAuth();
  const { language, t } = useLanguage();
  return <PaymentPage user={user} token={token} t={t} language={language} />;
};

const PaymentSuccessWrapper = () => {
  const { token } = useAuth();
  const { language, t } = useLanguage();
  return <PaymentSuccessPage token={token} t={t} language={language} />;
};

const PaymentPendingWrapper = () => {
  const { token } = useAuth();
  const { language } = useLanguage();
  return <PaymentPendingPage token={token} language={language} />;
};

const PaymentCancelWrapper = () => {
  const { language } = useLanguage();
  return <PaymentCancelPage language={language} />;
};

const AdminPaymentsWrapper = () => {
  const { token } = useAuth();
  const { language, t } = useLanguage();
  return (
    <Layout>
      <AdminPayments token={token} language={language} />
    </Layout>
  );
};

// ==================== MAIN APP ====================

function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AuthProvider>
          <SEOHead />
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/pricing" element={<PricingPage />} />
              <Route path="/payment" element={<PrivateRoute><PaymentPageWrapper /></PrivateRoute>} />
              <Route path="/payment/success" element={<PrivateRoute><PaymentSuccessWrapper /></PrivateRoute>} />
              <Route path="/payment/pending" element={<PrivateRoute><PaymentPendingWrapper /></PrivateRoute>} />
              <Route path="/payment/cancel" element={<PaymentCancelWrapper />} />
              <Route path="/payment/error" element={<PaymentCancelWrapper />} />
              <Route path="/dashboard" element={<PrivateRoute><DashboardRouter /></PrivateRoute>} />
              <Route path="/admin/dashboard" element={<PrivateRoute adminOnly><AdminDashboard /></PrivateRoute>} />
              <Route path="/admin/users" element={<PrivateRoute adminOnly><AdminUsers /></PrivateRoute>} />
              <Route path="/admin/cases" element={<PrivateRoute adminOnly><AdminAllCases /></PrivateRoute>} />
              <Route path="/admin/rules" element={<PrivateRoute adminOnly><AdminRules /></PrivateRoute>} />
              <Route path="/admin/api-settings" element={<PrivateRoute adminOnly><AdminAPISettings /></PrivateRoute>} />
              <Route path="/admin/email-settings" element={<PrivateRoute adminOnly><AdminEmailSettings /></PrivateRoute>} />
              <Route path="/admin/site-settings" element={<PrivateRoute adminOnly><AdminSiteSettings /></PrivateRoute>} />
              <Route path="/admin/payments" element={<PrivateRoute adminOnly><AdminPaymentsWrapper /></PrivateRoute>} />
              <Route path="/user/upload" element={<PrivateRoute><UserUpload /></PrivateRoute>} />
              <Route path="/user/cases" element={<PrivateRoute><UserCases /></PrivateRoute>} />
              <Route path="/case/:id" element={<PrivateRoute><CaseDetail /></PrivateRoute>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;
