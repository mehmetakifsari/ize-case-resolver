import React, { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Link, useNavigate, Navigate } from "react-router-dom";
import axios from "axios";
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, List, Settings, Home, Moon, Sun, Users, Key, LogOut, CreditCard, Zap, Shield, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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

  const register = async (email, password, full_name) => {
    const response = await axios.post(`${API}/auth/register`, {
      email,
      password,
      full_name,
      role: "user",
    });
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
    navigate("/dashboard");
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-950 dark:to-gray-900">
      {/* Header */}
      <nav className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <FileText className="w-8 h-8 text-primary" />
              <span className="text-xl font-bold">IZE Case Resolver</span>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" onClick={toggleTheme}>
                {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              </Button>
              <Button variant="ghost" onClick={() => navigate("/login")}>
                Giriş Yap
              </Button>
              <Button onClick={() => navigate("/register")}>
                Ücretsiz Başla
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-4" variant="outline">
            <Zap className="w-3 h-3 mr-1" />
            5 Ücretsiz Analiz ile Başlayın
          </Badge>
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
            IZE Dosyalarını AI ile<br />Anında Analiz Edin
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
            Yurtdışı garanti dosyalarınızı yapay zeka ile otomatik analiz edin. Garanti değerlendirmesi, email taslağı ve raporlama - hepsi bir arada.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" onClick={() => navigate("/register")} className="text-lg px-8">
              5 Ücretsiz Analiz Al
              <CheckCircle className="ml-2 w-5 h-5" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate("/pricing")}>
              Fiyatlandırma
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Özellikler</h2>
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

      {/* CTA */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-6">Hemen Başlayın</h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
            Kayıt olun ve ilk 5 analizinizi ücretsiz yapın
          </p>
          <Button size="lg" onClick={() => navigate("/register")} className="text-lg px-12">
            Ücretsiz Kayıt Ol
          </Button>
        </div>
      </section>

      {/* Footer */}
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
    navigate("/dashboard");
    return null;
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
      <Card className="w-full max-w-md">
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
              />
            </div>
            <div>
              <Label>Şifre</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
              />
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
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
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register, user } = useAuth();
  const navigate = useNavigate();

  if (user) {
    navigate("/dashboard");
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await register(email, password, fullName);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Kayıt başarısız");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
      <Card className="w-full max-w-md">
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
              <Label>Ad Soyad</Label>
              <Input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                placeholder="Adınız Soyadınız"
              />
            </div>
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="ornek@email.com"
              />
            </div>
            <div>
              <Label>Şifre</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                minLength={6}
              />
            </div>
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Kayıt yapılıyor..." : "Ücretsiz Kayıt Ol"}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            Zaten hesabınız var mı?{" "}
            <Link to="/login" className="text-primary hover:underline">
              Giriş Yap
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
          <h1 className="text-4xl font-bold mb-4">Fiyatlandırma</h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
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
              <Button className="w-full" onClick={() => navigate("/register")}>
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

  // Admin ise Admin Dashboard, User ise User Dashboard
  if (user.role === "admin") {
    return <Navigate to="/admin/dashboard" replace />;
  } else {
    return <Navigate to="/user/upload" replace />;
  }
};

// NOT: Admin ve User Dashboard'ları çok uzun olduğu için ayrı dosyalara taşınabilir
// Şimdilik basit versiyonlarını ekleyeceğim

// ==================== ADMIN LAYOUT ====================

const AdminLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white dark:bg-gray-900 border-r min-h-screen">
          <div className="p-4 border-b">
            <div className="flex items-center gap-2">
              <FileText className="w-8 h-8 text-primary" />
              <span className="font-bold">Admin Panel</span>
            </div>
          </div>
          <nav className="p-4 space-y-2">
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => navigate("/admin/dashboard")}
            >
              <Home className="w-4 h-4 mr-2" />
              Dashboard
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => navigate("/admin/users")}
            >
              <Users className="w-4 h-4 mr-2" />
              Kullanıcılar
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => navigate("/admin/cases")}
            >
              <List className="w-4 h-4 mr-2" />
              Tüm IZE'ler
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => navigate("/admin/rules")}
            >
              <FileText className="w-4 h-4 mr-2" />
              Garanti Kuralları
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => navigate("/admin/settings")}
            >
              <Key className="w-4 h-4 mr-2" />
              API Settings
            </Button>
            <Separator className="my-4" />
            <Button variant="ghost" className="w-full justify-start" onClick={toggleTheme}>
              {theme === "light" ? <Moon className="w-4 h-4 mr-2" /> : <Sun className="w-4 h-4 mr-2" />}
              {theme === "light" ? "Dark Mode" : "Light Mode"}
            </Button>
            <Button variant="ghost" className="w-full justify-start text-red-500" onClick={logout}>
              <LogOut className="w-4 h-4 mr-2" />
              Çıkış Yap
            </Button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
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

  useEffect(() => {
    fetchUser(); // Kredi güncellemeleri için
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <nav className="bg-white dark:bg-gray-900 border-b px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <FileText className="w-8 h-8 text-primary" />
              <span className="font-bold">IZE Case Resolver</span>
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={() => navigate("/user/upload")}>
                <Upload className="w-4 h-4 mr-2" />
                IZE Yükle
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate("/user/cases")}>
                <List className="w-4 h-4 mr-2" />
                Analizlerim
              </Button>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="text-sm">
              <CreditCard className="w-3 h-3 mr-1" />
              Kalan: {user?.free_analyses_remaining || 0}/5
            </Badge>
            <Button variant="ghost" size="sm" onClick={toggleTheme}>
              {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </Button>
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto p-8">{children}</main>
    </div>
  );
};

// Admin ve User sayfalarının basit versiyonları - gerçek implementasyon çok uzun olduğu için placeholder
const AdminDashboard = () => <AdminLayout><h1 className="text-3xl font-bold">Admin Dashboard</h1><p className="mt-4">İstatistikler burada gösterilecek...</p></AdminLayout>;
const AdminUsers = () => <AdminLayout><h1 className="text-3xl font-bold">Kullanıcı Yönetimi</h1><p className="mt-4">Kullanıcılar listesi...</p></AdminLayout>;
const AdminAllCases = () => <AdminLayout><h1 className="text-3xl font-bold">Tüm IZE Dosyaları</h1><p className="mt-4">Tüm case'ler...</p></AdminLayout>;
const AdminRules = () => <AdminLayout><h1 className="text-3xl font-bold">Garanti Kuralları</h1><p className="mt-4">Kurallar listesi...</p></AdminLayout>;
const AdminSettings = () => <AdminLayout><h1 className="text-3xl font-bold">API Settings</h1><p className="mt-4">OpenAI, Anthropic key'leri...</p></AdminLayout>;

const UserUpload = () => <UserLayout><h1 className="text-3xl font-bold">IZE Dosyası Yükle</h1><p className="mt-4">PDF yükleme formu...</p></UserLayout>;
const UserCases = () => <UserLayout><h1 className="text-3xl font-bold">Analizlerim</h1><p className="mt-4">Kendi case'leriniz...</p></UserLayout>;

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

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
