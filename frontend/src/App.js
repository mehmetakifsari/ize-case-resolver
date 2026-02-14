import React, { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Link, useNavigate, Navigate, useLocation } from "react-router-dom";
import axios from "axios";
import { 
  Upload, FileText, CheckCircle, XCircle, AlertCircle, List, Settings, Home, 
  Moon, Sun, Users, Key, LogOut, CreditCard, Zap, Shield, Clock, Menu, X,
  BarChart3, Archive, ChevronDown, ChevronRight, Plus, Trash2, Edit, Eye, EyeOff,
  Phone, Building, Mail, User, Lock
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Şubeler
const BRANCHES = ["Bursa", "İzmit", "Orhanlı", "Hadımköy", "Keşan"];

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
      console.error("Token geçersiz:", error);
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

// ==================== PROTECTED ROUTE ====================

const PrivateRoute = ({ children, adminOnly = false }) => {
  const { user, loading } = useAuth();

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

// ==================== LANDING PAGE ====================

const LandingPage = () => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
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
              <span className="text-xl font-bold">IZE Case Resolver</span>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" onClick={toggleTheme} data-testid="theme-toggle">
                {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              </Button>
              <Button variant="ghost" onClick={() => navigate("/login")} data-testid="login-btn">
                Giriş Yap
              </Button>
              <Button onClick={() => navigate("/register")} data-testid="register-btn">
                Ücretsiz Başla
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-4" variant="outline">
            <Zap className="w-3 h-3 mr-1" />
            5 Ücretsiz Analiz ile Başlayın
          </Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
            IZE Dosyalarını AI ile<br />Anında Analiz Edin
          </h1>
          <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
            Yurtdışı garanti dosyalarınızı yapay zeka ile otomatik analiz edin.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" onClick={() => navigate("/register")} data-testid="cta-register">
              5 Ücretsiz Analiz Al
              <CheckCircle className="ml-2 w-5 h-5" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate("/pricing")} data-testid="cta-pricing">
              Fiyatlandırma
            </Button>
          </div>
        </div>
      </section>

      <section className="py-20 px-4 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12">Özellikler</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <Upload className="w-10 h-10 text-primary mb-2" />
                <CardTitle>PDF Analizi</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">
                  Taranmış PDF'ler dahil tüm IZE dosyalarını OCR teknolojisi ile okuyun
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <Shield className="w-10 h-10 text-primary mb-2" />
                <CardTitle>Garanti Değerlendirmesi</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">
                  AI ile otomatik garanti kapsamı analizi ve karar gerekçeleri
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <Clock className="w-10 h-10 text-primary mb-2" />
                <CardTitle>Hızlı Sonuçlar</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">
                  Email taslağı, raporlama ve arşivleme - hepsi 1 dakikada
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <footer className="border-t py-8 px-4">
        <div className="max-w-7xl mx-auto text-center text-gray-600 dark:text-gray-400">
          <p>&copy; 2026 IZE Case Resolver. Tüm hakları saklıdır.</p>
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
      setError(err.response?.data?.detail || "Giriş başarısız");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
      <Card className="w-full max-w-md" data-testid="login-card">
        <CardHeader className="text-center">
          <FileText className="w-12 h-12 mx-auto mb-2 text-primary" />
          <CardTitle className="text-2xl">Giriş Yap</CardTitle>
          <CardDescription>IZE Case Resolver hesabınıza giriş yapın</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Email</Label>
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
              <Label>Şifre</Label>
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
              {loading ? "Giriş yapılıyor..." : "Giriş Yap"}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            Hesabınız yok mu?{" "}
            <Link to="/register" className="text-primary hover:underline">
              Kayıt Ol
            </Link>
          </div>
          <div className="mt-2 text-center">
            <Link to="/" className="text-sm text-gray-500 hover:underline">
              Ana Sayfaya Dön
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== REGISTER PAGE ====================

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    full_name: "",
    phone_number: "",
    branch: ""
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { register, user } = useAuth();
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
      setError("Şifreler eşleşmiyor");
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
        setError(detail || "Kayıt başarısız");
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
          <CardTitle className="text-2xl">Kayıt Ol</CardTitle>
          <CardDescription>
            <Badge variant="outline" className="mt-2">
              <Zap className="w-3 h-3 mr-1" />
              5 Ücretsiz Analiz Hakkı
            </Badge>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label className="flex items-center gap-1">
                <User className="w-4 h-4" /> Ad Soyad *
              </Label>
              <Input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                required
                placeholder="Adınız Soyadınız"
                data-testid="register-fullname"
              />
            </div>
            <div>
              <Label className="flex items-center gap-1">
                <Mail className="w-4 h-4" /> Email *
              </Label>
              <Input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="ornek@email.com"
                data-testid="register-email"
              />
            </div>
            <div>
              <Label className="flex items-center gap-1">
                <Phone className="w-4 h-4" /> Telefon
              </Label>
              <Input
                type="tel"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="5XX XXX XXXX"
                data-testid="register-phone"
              />
            </div>
            <div>
              <Label className="flex items-center gap-1">
                <Building className="w-4 h-4" /> Şube
              </Label>
              <Select 
                value={formData.branch} 
                onValueChange={(value) => setFormData({...formData, branch: value})}
              >
                <SelectTrigger data-testid="register-branch">
                  <SelectValue placeholder="Şube seçin" />
                </SelectTrigger>
                <SelectContent>
                  {BRANCHES.map(b => (
                    <SelectItem key={b} value={b}>{b}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="flex items-center gap-1">
                <Lock className="w-4 h-4" /> Şifre *
              </Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  placeholder="********"
                  data-testid="register-password"
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
              <p className="text-xs text-gray-500 mt-1">
                En az 8 karakter, büyük/küçük harf ve özel karakter içermelidir
              </p>
            </div>
            <div>
              <Label>Şifre Tekrar *</Label>
              <Input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                placeholder="********"
                data-testid="register-confirm-password"
              />
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full" disabled={loading} data-testid="register-submit">
              {loading ? "Kayıt yapılıyor..." : "Ücretsiz Kayıt Ol"}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            Zaten hesabınız var mı?{" "}
            <Link to="/login" className="text-primary hover:underline">
              Giriş Yap
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== PRICING PAGE ====================

const PricingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <nav className="border-b bg-white dark:bg-gray-900 px-4 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <FileText className="w-8 h-8 text-primary" />
            <span className="text-xl font-bold">IZE Case Resolver</span>
          </Link>
          <Button variant="ghost" onClick={() => navigate("/")}>
            Ana Sayfa
          </Button>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">Fiyatlandırma</h1>
          <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400">
            İhtiyacınıza uygun planı seçin
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <Card className="border-2">
            <CardHeader>
              <CardTitle className="text-2xl">Ücretsiz</CardTitle>
              <CardDescription className="text-lg">Başlamak için ideal</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-4xl font-bold">0₺</div>
              <ul className="space-y-2">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  5 Ücretsiz Analiz
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  PDF Okuma (OCR)
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  AI Analizi
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  Email Taslağı
                </li>
              </ul>
              <Button className="w-full" onClick={() => navigate("/register")} data-testid="pricing-free-btn">
                Ücretsiz Başla
              </Button>
            </CardContent>
          </Card>

          <Card className="border-2 border-primary relative">
            <div className="absolute top-0 right-0 bg-primary text-white px-4 py-1 text-sm rounded-bl-lg">
              Yakında
            </div>
            <CardHeader>
              <CardTitle className="text-2xl">Pro</CardTitle>
              <CardDescription className="text-lg">Profesyonel kullanım</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-4xl font-bold">Yakında...</div>
              <ul className="space-y-2 text-gray-500">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Sınırsız Analiz
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Öncelikli Destek
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  API Erişimi
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" />
                  Özel Raporlar
                </li>
              </ul>
              <Button className="w-full" disabled>
                Çok Yakında
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// ==================== DASHBOARD ROUTER ====================

const DashboardRouter = () => {
  const { user } = useAuth();

  if (!user) return null;

  if (user.role === "admin") {
    return <Navigate to="/admin/dashboard" replace />;
  } else {
    return <Navigate to="/user/upload" replace />;
  }
};

// ==================== ADMIN LAYOUT ====================

const AdminLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const menuItems = [
    { path: "/admin/dashboard", icon: BarChart3, label: "Dashboard" },
    { path: "/admin/users", icon: Users, label: "Kullanıcılar" },
    { path: "/admin/cases", icon: List, label: "Tüm IZE'ler" },
    { path: "/admin/rules", icon: FileText, label: "Garanti Kuralları" },
    { path: "/admin/settings", icon: Key, label: "API Ayarları" },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Mobile Header */}
      <div className="lg:hidden bg-white dark:bg-gray-900 border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-6 h-6 text-primary" />
          <span className="font-bold">Admin Panel</span>
        </div>
        <Button variant="ghost" size="sm" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </Button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-white dark:bg-gray-900 border-b px-4 py-4 space-y-2">
          {menuItems.map((item) => (
            <Button
              key={item.path}
              variant={isActive(item.path) ? "secondary" : "ghost"}
              className="w-full justify-start"
              onClick={() => { navigate(item.path); setMobileMenuOpen(false); }}
            >
              <item.icon className="w-4 h-4 mr-2" />
              {item.label}
            </Button>
          ))}
          <Separator />
          <Button variant="ghost" className="w-full justify-start" onClick={toggleTheme}>
            {theme === "light" ? <Moon className="w-4 h-4 mr-2" /> : <Sun className="w-4 h-4 mr-2" />}
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </Button>
          <Button variant="ghost" className="w-full justify-start text-red-500" onClick={logout}>
            <LogOut className="w-4 h-4 mr-2" />
            Çıkış Yap
          </Button>
        </div>
      )}

      <div className="flex">
        {/* Desktop Sidebar */}
        <aside className={`hidden lg:block ${sidebarOpen ? 'w-64' : 'w-16'} bg-white dark:bg-gray-900 border-r min-h-screen transition-all duration-300`}>
          <div className="p-4 border-b flex items-center justify-between">
            {sidebarOpen && (
              <div className="flex items-center gap-2">
                <FileText className="w-8 h-8 text-primary" />
                <span className="font-bold">Admin Panel</span>
              </div>
            )}
            <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(!sidebarOpen)}>
              {sidebarOpen ? <ChevronDown className="w-4 h-4 rotate-90" /> : <ChevronRight className="w-4 h-4" />}
            </Button>
          </div>
          <nav className="p-4 space-y-2">
            {menuItems.map((item) => (
              <Button
                key={item.path}
                variant={isActive(item.path) ? "secondary" : "ghost"}
                className={`w-full ${sidebarOpen ? 'justify-start' : 'justify-center'}`}
                onClick={() => navigate(item.path)}
                data-testid={`nav-${item.path.split('/').pop()}`}
              >
                <item.icon className="w-4 h-4" />
                {sidebarOpen && <span className="ml-2">{item.label}</span>}
              </Button>
            ))}
            <Separator className="my-4" />
            <Button variant="ghost" className={`w-full ${sidebarOpen ? 'justify-start' : 'justify-center'}`} onClick={toggleTheme}>
              {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              {sidebarOpen && <span className="ml-2">{theme === "light" ? "Dark Mode" : "Light Mode"}</span>}
            </Button>
            <Button variant="ghost" className={`w-full ${sidebarOpen ? 'justify-start' : 'justify-center'} text-red-500`} onClick={logout}>
              <LogOut className="w-4 h-4" />
              {sidebarOpen && <span className="ml-2">Çıkış Yap</span>}
            </Button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-4 lg:p-8">
          <div className="mb-6">
            <p className="text-sm text-gray-500">
              Hoş geldin, <strong>{user?.full_name}</strong> (Admin)
            </p>
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
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    fetchUser();
  }, []);

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <nav className="bg-white dark:bg-gray-900 border-b px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <FileText className="w-6 sm:w-8 h-6 sm:h-8 text-primary" />
              <span className="font-bold hidden sm:inline">IZE Case Resolver</span>
            </div>
            <div className="hidden sm:flex gap-2">
              <Button 
                variant={isActive("/user/upload") ? "secondary" : "ghost"} 
                size="sm" 
                onClick={() => navigate("/user/upload")}
                data-testid="nav-upload"
              >
                <Upload className="w-4 h-4 mr-2" />
                IZE Yükle
              </Button>
              <Button 
                variant={isActive("/user/cases") ? "secondary" : "ghost"} 
                size="sm" 
                onClick={() => navigate("/user/cases")}
                data-testid="nav-cases"
              >
                <List className="w-4 h-4 mr-2" />
                Analizlerim
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <Badge variant="outline" className="text-xs sm:text-sm">
              <CreditCard className="w-3 h-3 mr-1" />
              <span className="hidden sm:inline">Kalan:</span> {user?.free_analyses_remaining || 0}
            </Badge>
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
        
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden mt-3 pt-3 border-t space-y-2">
            <Button variant="ghost" className="w-full justify-start" onClick={() => { navigate("/user/upload"); setMobileMenuOpen(false); }}>
              <Upload className="w-4 h-4 mr-2" />
              IZE Yükle
            </Button>
            <Button variant="ghost" className="w-full justify-start" onClick={() => { navigate("/user/cases"); setMobileMenuOpen(false); }}>
              <List className="w-4 h-4 mr-2" />
              Analizlerim
            </Button>
            <Button variant="ghost" className="w-full justify-start" onClick={toggleTheme}>
              {theme === "light" ? <Moon className="w-4 h-4 mr-2" /> : <Sun className="w-4 h-4 mr-2" />}
              {theme === "light" ? "Dark Mode" : "Light Mode"}
            </Button>
            <Button variant="ghost" className="w-full justify-start text-red-500" onClick={logout}>
              <LogOut className="w-4 h-4 mr-2" />
              Çıkış Yap
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

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/admin/analytics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error("Analytics yüklenemedi:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <h1 className="text-2xl sm:text-3xl font-bold mb-6" data-testid="admin-dashboard-title">Dashboard</h1>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Toplam Kullanıcı</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold" data-testid="stat-total-users">{analytics?.users?.total || 0}</div>
            <p className="text-xs text-green-600">{analytics?.users?.active || 0} aktif</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Toplam IZE</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold" data-testid="stat-total-cases">{analytics?.cases?.total || 0}</div>
            <p className="text-xs text-gray-500">{analytics?.cases?.archived || 0} arşivde</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Bu Hafta</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary">{analytics?.cases?.recent_week || 0}</div>
            <p className="text-xs text-gray-500">yeni analiz</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Garanti Kapsamı</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{analytics?.decisions?.COVERED || 0}</div>
            <p className="text-xs text-red-500">{analytics?.decisions?.OUT_OF_COVERAGE || 0} kapsam dışı</p>
          </CardContent>
        </Card>
      </div>

      {/* Branch Distribution */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Şubelere Göre Dağılım</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics?.branches && Object.entries(analytics.branches).map(([branch, count]) => (
                <div key={branch} className="flex items-center justify-between">
                  <span className="text-sm">{branch}</span>
                  <Badge variant="outline">{count}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Garanti Kararları</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  Kapsam İçi
                </span>
                <Badge className="bg-green-100 text-green-800">{analytics?.decisions?.COVERED || 0}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm flex items-center gap-2">
                  <XCircle className="w-4 h-4 text-red-500" />
                  Kapsam Dışı
                </span>
                <Badge className="bg-red-100 text-red-800">{analytics?.decisions?.OUT_OF_COVERAGE || 0}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-yellow-500" />
                  Ek Bilgi Gerekli
                </span>
                <Badge className="bg-yellow-100 text-yellow-800">{analytics?.decisions?.ADDITIONAL_INFO_REQUIRED || 0}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
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

  useEffect(() => {
    fetchUsers();
  }, [filter]);

  const fetchUsers = async () => {
    try {
      let url = `${API}/admin/users`;
      const params = new URLSearchParams();
      if (filter.branch) params.append("branch", filter.branch);
      if (filter.role) params.append("role", filter.role);
      if (params.toString()) url += `?${params.toString()}`;

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      console.error("Kullanıcılar yüklenemedi:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleActive = async (userId) => {
    try {
      await axios.patch(`${API}/admin/users/${userId}/toggle-active`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchUsers();
    } catch (error) {
      console.error("Durum güncellenemedi:", error);
    }
  };

  const addCredit = async (userId) => {
    try {
      await axios.patch(`${API}/admin/users/${userId}/add-credit?amount=5`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchUsers();
    } catch (error) {
      console.error("Kredi eklenemedi:", error);
    }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm("Bu kullanıcıyı silmek istediğinize emin misiniz?")) return;
    try {
      await axios.delete(`${API}/admin/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchUsers();
    } catch (error) {
      alert(error.response?.data?.detail || "Kullanıcı silinemedi");
    }
  };

  return (
    <AdminLayout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold" data-testid="admin-users-title">Kullanıcı Yönetimi</h1>
        <div className="flex gap-2">
          <Select value={filter.branch} onValueChange={(v) => setFilter({...filter, branch: v})}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Tüm Şubeler" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Tüm Şubeler</SelectItem>
              {BRANCHES.map(b => <SelectItem key={b} value={b}>{b}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filter.role} onValueChange={(v) => setFilter({...filter, role: v})}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Tüm Roller" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Tüm Roller</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
              <SelectItem value="user">User</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {users.map(user => (
            <Card key={user.id} data-testid={`user-card-${user.id}`}>
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{user.full_name}</span>
                      <Badge variant={user.role === "admin" ? "default" : "outline"}>
                        {user.role}
                      </Badge>
                      <Badge variant={user.is_active ? "default" : "destructive"}>
                        {user.is_active ? "Aktif" : "Pasif"}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-500">{user.email}</p>
                    <div className="flex gap-4 text-xs text-gray-500">
                      {user.phone_number && <span><Phone className="w-3 h-3 inline mr-1" />{user.phone_number}</span>}
                      {user.branch && <span><Building className="w-3 h-3 inline mr-1" />{user.branch}</span>}
                      <span><CreditCard className="w-3 h-3 inline mr-1" />Kredi: {user.free_analyses_remaining}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => addCredit(user.id)}>
                      <Plus className="w-4 h-4 mr-1" />5 Kredi
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => toggleActive(user.id)}>
                      {user.is_active ? "Pasif Yap" : "Aktif Yap"}
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => deleteUser(user.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {users.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center text-gray-500">
                Kullanıcı bulunamadı
              </CardContent>
            </Card>
          )}
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
  const navigate = useNavigate();

  useEffect(() => {
    fetchCases();
  }, [filter]);

  const fetchCases = async () => {
    try {
      let url = `${API}/admin/cases`;
      const params = new URLSearchParams();
      if (filter.branch) params.append("branch", filter.branch);
      if (filter.archived !== "") params.append("archived", filter.archived);
      if (params.toString()) url += `?${params.toString()}`;

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(response.data);
    } catch (error) {
      console.error("Case'ler yüklenemedi:", error);
    } finally {
      setLoading(false);
    }
  };

  const archiveCase = async (caseId) => {
    try {
      await axios.patch(`${API}/admin/cases/${caseId}/archive`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCases();
    } catch (error) {
      console.error("Arşivleme başarısız:", error);
    }
  };

  const deleteCase = async (caseId) => {
    if (!window.confirm("Bu case'i silmek istediğinize emin misiniz?")) return;
    try {
      await axios.delete(`${API}/admin/cases/${caseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCases();
    } catch (error) {
      console.error("Silme başarısız:", error);
    }
  };

  const getDecisionBadge = (decision) => {
    const colors = {
      "COVERED": "bg-green-100 text-green-800",
      "OUT_OF_COVERAGE": "bg-red-100 text-red-800",
      "ADDITIONAL_INFO_REQUIRED": "bg-yellow-100 text-yellow-800"
    };
    return colors[decision] || "bg-gray-100 text-gray-800";
  };

  return (
    <AdminLayout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold" data-testid="admin-cases-title">Tüm IZE Dosyaları</h1>
        <div className="flex gap-2">
          <Select value={filter.branch} onValueChange={(v) => setFilter({...filter, branch: v})}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Tüm Şubeler" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Tüm Şubeler</SelectItem>
              {BRANCHES.map(b => <SelectItem key={b} value={b}>{b}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filter.archived} onValueChange={(v) => setFilter({...filter, archived: v})}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Tümü" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Tümü</SelectItem>
              <SelectItem value="false">Aktif</SelectItem>
              <SelectItem value="true">Arşiv</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {cases.map(c => (
            <Card key={c.id} className={c.is_archived ? "opacity-60" : ""} data-testid={`case-card-${c.id}`}>
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium">{c.ize_no}</span>
                      <Badge className={getDecisionBadge(c.warranty_decision)}>
                        {c.warranty_decision}
                      </Badge>
                      {c.is_archived && <Badge variant="secondary"><Archive className="w-3 h-3 mr-1" />Arşiv</Badge>}
                    </div>
                    <p className="text-sm text-gray-500">{c.company} - {c.case_title}</p>
                    <div className="flex gap-4 text-xs text-gray-500">
                      {c.branch && <span><Building className="w-3 h-3 inline mr-1" />{c.branch}</span>}
                      <span>{new Date(c.created_at).toLocaleDateString('tr-TR')}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => navigate(`/case/${c.id}`)}>
                      <Eye className="w-4 h-4 mr-1" />Görüntüle
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => archiveCase(c.id)}>
                      <Archive className="w-4 h-4 mr-1" />{c.is_archived ? "Çıkar" : "Arşivle"}
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => deleteCase(c.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {cases.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center text-gray-500">
                Case bulunamadı
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </AdminLayout>
  );
};

// ==================== ADMIN RULES ====================

const AdminRules = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ rule_version: "", rule_text: "", keywords: "" });
  const { token } = useAuth();

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await axios.get(`${API}/warranty-rules`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRules(response.data);
    } catch (error) {
      console.error("Kurallar yüklenemedi:", error);
    } finally {
      setLoading(false);
    }
  };

  const createRule = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/warranty-rules`, {
        rule_version: formData.rule_version,
        rule_text: formData.rule_text,
        keywords: formData.keywords.split(",").map(k => k.trim()).filter(k => k)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowForm(false);
      setFormData({ rule_version: "", rule_text: "", keywords: "" });
      fetchRules();
    } catch (error) {
      alert("Kural eklenemedi: " + (error.response?.data?.detail || error.message));
    }
  };

  const deleteRule = async (ruleId) => {
    if (!window.confirm("Bu kuralı silmek istediğinize emin misiniz?")) return;
    try {
      await axios.delete(`${API}/warranty-rules/${ruleId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchRules();
    } catch (error) {
      console.error("Silme başarısız:", error);
    }
  };

  return (
    <AdminLayout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold" data-testid="admin-rules-title">Garanti Kuralları</h1>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="w-4 h-4 mr-2" />Yeni Kural
        </Button>
      </div>

      {showForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Yeni Garanti Kuralı</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={createRule} className="space-y-4">
              <div>
                <Label>Versiyon</Label>
                <Input
                  value={formData.rule_version}
                  onChange={(e) => setFormData({...formData, rule_version: e.target.value})}
                  required
                  placeholder="1.0"
                />
              </div>
              <div>
                <Label>Kural Metni</Label>
                <textarea
                  className="w-full p-2 border rounded-md min-h-[100px] bg-background"
                  value={formData.rule_text}
                  onChange={(e) => setFormData({...formData, rule_text: e.target.value})}
                  required
                  placeholder="Garanti kuralı metni..."
                />
              </div>
              <div>
                <Label>Anahtar Kelimeler (virgülle ayırın)</Label>
                <Input
                  value={formData.keywords}
                  onChange={(e) => setFormData({...formData, keywords: e.target.value})}
                  placeholder="garanti, warranty, 2 yıl"
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit">Kaydet</Button>
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>İptal</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {rules.map(rule => (
            <Card key={rule.id}>
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    <div className="flex items-center gap-2">
                      <Badge>v{rule.rule_version}</Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(rule.created_at).toLocaleDateString('tr-TR')}
                      </span>
                    </div>
                    <p className="text-sm">{rule.rule_text}</p>
                    {rule.keywords?.length > 0 && (
                      <div className="flex gap-1 flex-wrap">
                        {rule.keywords.map((k, i) => (
                          <Badge key={i} variant="outline" className="text-xs">{k}</Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <Button size="sm" variant="destructive" onClick={() => deleteRule(rule.id)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
          {rules.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center text-gray-500">
                Henüz kural eklenmemiş
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </AdminLayout>
  );
};

// ==================== ADMIN SETTINGS ====================

const AdminSettings = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    openai_key: "",
    anthropic_key: "",
    google_key: ""
  });
  const [showKeys, setShowKeys] = useState({});
  const { token } = useAuth();

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSettings(response.data);
    } catch (error) {
      console.error("Ayarlar yüklenemedi:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateSettings = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updateData = {};
      if (formData.openai_key) updateData.openai_key = formData.openai_key;
      if (formData.anthropic_key) updateData.anthropic_key = formData.anthropic_key;
      if (formData.google_key) updateData.google_key = formData.google_key;

      await axios.put(`${API}/admin/settings`, updateData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFormData({ openai_key: "", anthropic_key: "", google_key: "" });
      fetchSettings();
      alert("Ayarlar güncellendi");
    } catch (error) {
      alert("Güncelleme başarısız: " + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <h1 className="text-2xl sm:text-3xl font-bold mb-6" data-testid="admin-settings-title">API Ayarları</h1>

      <div className="grid gap-6">
        {/* Current Keys */}
        <Card>
          <CardHeader>
            <CardTitle>Mevcut API Anahtarları</CardTitle>
            <CardDescription>Maskelenmiş API key'leriniz</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>OpenAI API Key</Label>
                <p className="text-sm text-gray-500 font-mono">
                  {settings?.openai_key_masked || "Ayarlanmamış"}
                </p>
              </div>
              <Badge variant={settings?.openai_key ? "default" : "outline"}>
                {settings?.openai_key ? "Aktif" : "Yok"}
              </Badge>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <Label>Anthropic API Key</Label>
                <p className="text-sm text-gray-500 font-mono">
                  {settings?.anthropic_key_masked || "Ayarlanmamış"}
                </p>
              </div>
              <Badge variant={settings?.anthropic_key ? "default" : "outline"}>
                {settings?.anthropic_key ? "Aktif" : "Yok"}
              </Badge>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <Label>Google API Key</Label>
                <p className="text-sm text-gray-500 font-mono">
                  {settings?.google_key_masked || "Ayarlanmamış"}
                </p>
              </div>
              <Badge variant={settings?.google_key ? "default" : "outline"}>
                {settings?.google_key ? "Aktif" : "Yok"}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Update Keys */}
        <Card>
          <CardHeader>
            <CardTitle>API Anahtarlarını Güncelle</CardTitle>
            <CardDescription>Yeni key girmek için aşağıdaki alanları doldurun</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={updateSettings} className="space-y-4">
              <div>
                <Label>Yeni OpenAI API Key</Label>
                <div className="relative">
                  <Input
                    type={showKeys.openai ? "text" : "password"}
                    value={formData.openai_key}
                    onChange={(e) => setFormData({...formData, openai_key: e.target.value})}
                    placeholder="sk-..."
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowKeys({...showKeys, openai: !showKeys.openai})}
                  >
                    {showKeys.openai ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
              <div>
                <Label>Yeni Anthropic API Key</Label>
                <div className="relative">
                  <Input
                    type={showKeys.anthropic ? "text" : "password"}
                    value={formData.anthropic_key}
                    onChange={(e) => setFormData({...formData, anthropic_key: e.target.value})}
                    placeholder="sk-ant-..."
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowKeys({...showKeys, anthropic: !showKeys.anthropic})}
                  >
                    {showKeys.anthropic ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
              <div>
                <Label>Yeni Google API Key</Label>
                <div className="relative">
                  <Input
                    type={showKeys.google ? "text" : "password"}
                    value={formData.google_key}
                    onChange={(e) => setFormData({...formData, google_key: e.target.value})}
                    placeholder="AIza..."
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowKeys({...showKeys, google: !showKeys.google})}
                  >
                    {showKeys.google ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
              <Button type="submit" disabled={saving}>
                {saving ? "Kaydediliyor..." : "Kaydet"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
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
  const navigate = useNavigate();

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      if (branch) {
        formData.append("branch", branch);
      }

      const response = await axios.post(`${API}/cases/analyze`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data"
        }
      });

      fetchUser();
      navigate(`/case/${response.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Yükleme başarısız");
    } finally {
      setUploading(false);
    }
  };

  return (
    <UserLayout>
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl sm:text-3xl font-bold mb-6" data-testid="user-upload-title">IZE Dosyası Yükle</h1>
        
        {user?.free_analyses_remaining <= 0 && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Ücretsiz analiz hakkınız bitti. Lütfen yönetici ile iletişime geçin.
            </AlertDescription>
          </Alert>
        )}

        <Card>
          <CardContent className="p-6">
            <form onSubmit={handleUpload} className="space-y-6">
              <div>
                <Label>PDF Dosyası</Label>
                <div 
                  className={`mt-2 border-2 border-dashed rounded-lg p-8 text-center ${
                    file ? 'border-primary bg-primary/5' : 'border-gray-300'
                  }`}
                >
                  <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setFile(e.target.files[0])}
                    className="hidden"
                    id="pdf-upload"
                    data-testid="file-input"
                  />
                  <label htmlFor="pdf-upload" className="cursor-pointer">
                    <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                    {file ? (
                      <p className="text-primary font-medium">{file.name}</p>
                    ) : (
                      <>
                        <p className="text-gray-600">PDF dosyanızı sürükleyin veya seçin</p>
                        <p className="text-sm text-gray-400 mt-1">Maksimum 10MB</p>
                      </>
                    )}
                  </label>
                </div>
              </div>

              <div>
                <Label>Şube (Opsiyonel)</Label>
                <Select value={branch} onValueChange={setBranch}>
                  <SelectTrigger data-testid="upload-branch">
                    <SelectValue placeholder="Şube seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {BRANCHES.map(b => (
                      <SelectItem key={b} value={b}>{b}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button 
                type="submit" 
                className="w-full" 
                disabled={!file || uploading || user?.free_analyses_remaining <= 0}
                data-testid="upload-submit"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Analiz ediliyor...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Analiz Et
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </UserLayout>
  );
};

// ==================== USER CASES ====================

const UserCases = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const response = await axios.get(`${API}/cases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(response.data);
    } catch (error) {
      console.error("Case'ler yüklenemedi:", error);
    } finally {
      setLoading(false);
    }
  };

  const getDecisionBadge = (decision) => {
    const colors = {
      "COVERED": "bg-green-100 text-green-800",
      "OUT_OF_COVERAGE": "bg-red-100 text-red-800",
      "ADDITIONAL_INFO_REQUIRED": "bg-yellow-100 text-yellow-800"
    };
    return colors[decision] || "bg-gray-100 text-gray-800";
  };

  return (
    <UserLayout>
      <h1 className="text-2xl sm:text-3xl font-bold mb-6" data-testid="user-cases-title">Analizlerim</h1>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {cases.map(c => (
            <Card 
              key={c.id} 
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/case/${c.id}`)}
              data-testid={`case-item-${c.id}`}
            >
              <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{c.ize_no}</span>
                      <Badge className={getDecisionBadge(c.warranty_decision)}>
                        {c.warranty_decision === "COVERED" ? "Kapsam İçi" : 
                         c.warranty_decision === "OUT_OF_COVERAGE" ? "Kapsam Dışı" : "Ek Bilgi"}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-500">{c.company}</p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(c.created_at).toLocaleDateString('tr-TR')}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
          {cases.length === 0 && (
            <Card>
              <CardContent className="p-8 text-center">
                <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">Henüz analiz yapmadınız</p>
                <Button className="mt-4" onClick={() => navigate("/user/upload")}>
                  İlk Analizinizi Yapın
                </Button>
              </CardContent>
            </Card>
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
  const [expandedSections, setExpandedSections] = useState({
    vehicle: true,
    warranty: true,
    operations: false,
    email: false
  });
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const caseId = window.location.pathname.split('/').pop();

  useEffect(() => {
    fetchCase();
  }, [caseId]);

  const fetchCase = async () => {
    try {
      const response = await axios.get(`${API}/cases/${caseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCaseData(response.data);
    } catch (error) {
      console.error("Case yüklenemedi:", error);
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({...prev, [section]: !prev[section]}));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!caseData) return null;

  const Layout = user?.role === "admin" ? AdminLayout : UserLayout;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <Button variant="ghost" className="mb-4" onClick={() => navigate(-1)}>
          &larr; Geri
        </Button>

        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold" data-testid="case-detail-title">{caseData.case_title}</h1>
          <p className="text-gray-500">IZE No: {caseData.ize_no}</p>
        </div>

        <div className="space-y-4">
          {/* Araç Bilgileri */}
          <Card>
            <CardHeader 
              className="cursor-pointer" 
              onClick={() => toggleSection('vehicle')}
            >
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Araç Bilgileri</CardTitle>
                {expandedSections.vehicle ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </div>
            </CardHeader>
            {expandedSections.vehicle && (
              <CardContent className="space-y-2">
                <div className="grid grid-cols-2 gap-4">
                  <div><span className="text-gray-500">Firma:</span> {caseData.company}</div>
                  <div><span className="text-gray-500">Plaka:</span> {caseData.plate}</div>
                  <div><span className="text-gray-500">VIN:</span> {caseData.vin}</div>
                  <div><span className="text-gray-500">KM:</span> {caseData.repair_km?.toLocaleString()}</div>
                  <div><span className="text-gray-500">Garanti Başlangıç:</span> {caseData.warranty_start_date}</div>
                  <div><span className="text-gray-500">Onarım Tarihi:</span> {caseData.repair_date}</div>
                  <div><span className="text-gray-500">Araç Yaşı:</span> {caseData.vehicle_age_months} ay</div>
                  {caseData.branch && <div><span className="text-gray-500">Şube:</span> {caseData.branch}</div>}
                </div>
              </CardContent>
            )}
          </Card>

          {/* Garanti Değerlendirmesi */}
          <Card>
            <CardHeader 
              className="cursor-pointer" 
              onClick={() => toggleSection('warranty')}
            >
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  Garanti Değerlendirmesi
                  <Badge className={
                    caseData.warranty_decision === "COVERED" ? "bg-green-100 text-green-800" :
                    caseData.warranty_decision === "OUT_OF_COVERAGE" ? "bg-red-100 text-red-800" :
                    "bg-yellow-100 text-yellow-800"
                  }>
                    {caseData.warranty_decision}
                  </Badge>
                </CardTitle>
                {expandedSections.warranty ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </div>
            </CardHeader>
            {expandedSections.warranty && (
              <CardContent className="space-y-4">
                <div>
                  <span className="text-gray-500">2 Yıl Garanti İçinde:</span>{" "}
                  {caseData.is_within_2_year_warranty ? 
                    <Badge className="bg-green-100 text-green-800">Evet</Badge> : 
                    <Badge className="bg-red-100 text-red-800">Hayır</Badge>}
                </div>
                {caseData.decision_rationale?.length > 0 && (
                  <div>
                    <span className="text-gray-500 block mb-2">Karar Gerekçeleri:</span>
                    <ul className="list-disc list-inside space-y-1">
                      {caseData.decision_rationale.map((r, i) => (
                        <li key={i} className="text-sm">{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Arıza Şikayeti:</span>
                  <p className="text-sm mt-1">{caseData.failure_complaint || "-"}</p>
                </div>
                <div>
                  <span className="text-gray-500">Arıza Nedeni:</span>
                  <p className="text-sm mt-1">{caseData.failure_cause || "-"}</p>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Yapılan İşlemler */}
          <Card>
            <CardHeader 
              className="cursor-pointer" 
              onClick={() => toggleSection('operations')}
            >
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Yapılan İşlemler & Parçalar</CardTitle>
                {expandedSections.operations ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </div>
            </CardHeader>
            {expandedSections.operations && (
              <CardContent className="space-y-4">
                {caseData.operations_performed?.length > 0 && (
                  <div>
                    <span className="text-gray-500 block mb-2">İşlemler:</span>
                    <ul className="list-disc list-inside space-y-1">
                      {caseData.operations_performed.map((op, i) => (
                        <li key={i} className="text-sm">{op}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {caseData.parts_replaced?.length > 0 && (
                  <div>
                    <span className="text-gray-500 block mb-2">Değiştirilen Parçalar:</span>
                    <div className="space-y-2">
                      {caseData.parts_replaced.map((part, i) => (
                        <div key={i} className="bg-gray-50 dark:bg-gray-800 p-2 rounded text-sm">
                          <strong>{part.partName}</strong> x{part.qty}
                          {part.description && <p className="text-gray-500 text-xs">{part.description}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Onarım Özeti:</span>
                  <p className="text-sm mt-1">{caseData.repair_process_summary || "-"}</p>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Email Taslağı */}
          <Card>
            <CardHeader 
              className="cursor-pointer" 
              onClick={() => toggleSection('email')}
            >
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Email Taslağı</CardTitle>
                {expandedSections.email ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </div>
            </CardHeader>
            {expandedSections.email && (
              <CardContent className="space-y-4">
                <div>
                  <span className="text-gray-500">Konu:</span>
                  <p className="text-sm mt-1 font-medium">{caseData.email_subject}</p>
                </div>
                <div>
                  <span className="text-gray-500">İçerik:</span>
                  <div className="mt-2 bg-gray-50 dark:bg-gray-800 p-4 rounded whitespace-pre-wrap text-sm">
                    {caseData.email_body}
                  </div>
                </div>
                <Button 
                  variant="outline"
                  onClick={() => navigator.clipboard.writeText(caseData.email_body)}
                >
                  Email Metnini Kopyala
                </Button>
              </CardContent>
            )}
          </Card>
        </div>
      </div>
    </Layout>
  );
};

// ==================== MAIN APP ====================

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/pricing" element={<PricingPage />} />

            {/* Dashboard Router */}
            <Route path="/dashboard" element={<PrivateRoute><DashboardRouter /></PrivateRoute>} />

            {/* Admin Routes */}
            <Route path="/admin/dashboard" element={<PrivateRoute adminOnly><AdminDashboard /></PrivateRoute>} />
            <Route path="/admin/users" element={<PrivateRoute adminOnly><AdminUsers /></PrivateRoute>} />
            <Route path="/admin/cases" element={<PrivateRoute adminOnly><AdminAllCases /></PrivateRoute>} />
            <Route path="/admin/rules" element={<PrivateRoute adminOnly><AdminRules /></PrivateRoute>} />
            <Route path="/admin/settings" element={<PrivateRoute adminOnly><AdminSettings /></PrivateRoute>} />

            {/* User Routes */}
            <Route path="/user/upload" element={<PrivateRoute><UserUpload /></PrivateRoute>} />
            <Route path="/user/cases" element={<PrivateRoute><UserCases /></PrivateRoute>} />

            {/* Case Detail */}
            <Route path="/case/:id" element={<PrivateRoute><CaseDetail /></PrivateRoute>} />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
