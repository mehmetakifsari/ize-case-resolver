import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, List, Settings, Home, Moon, Sun, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Theme Context
const ThemeContext = React.createContext();

const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("theme") || "light";
  });

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

const useTheme = () => {
  const context = React.useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider");
  return context;
};

// Ana Sayfa - PDF Yükleme ve Analiz
const HomePage = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === "application/pdf") {
      setFile(selectedFile);
      setError(null);
    } else {
      setError("Lütfen geçerli bir PDF dosyası seçin");
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Lütfen bir dosya seçin");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(`${API}/analyze`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setResult(response.data);
      setTimeout(() => {
        navigate(`/case/${response.data.id}`);
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || "Analiz sırasında bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 px-4">
      <Card className="border-2 border-dashed dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg md:text-xl">
            <Upload className="w-5 h-5 md:w-6 md:h-6" />
            IZE Dosyası Yükle ve Analiz Et
          </CardTitle>
          <CardDescription className="text-sm">
            Yurtdışı garanti IZE PDF dosyasını yükleyin. Sistem otomatik olarak analiz edip garanti değerlendirmesi yapacaktır.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="hidden"
              id="pdf-upload"
              disabled={loading}
            />
            <label htmlFor="pdf-upload" className="flex-1 cursor-pointer">
              <div className="border-2 border-dashed rounded-lg p-6 md:p-8 text-center hover:border-primary transition-colors dark:border-gray-700 dark:hover:border-primary">
                <FileText className="w-10 h-10 md:w-12 md:h-12 mx-auto mb-2 text-gray-400 dark:text-gray-500" />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {file ? file.name : "PDF dosyası seçmek için tıklayın"}
                </p>
              </div>
            </label>
          </div>

          {file && (
            <Button
              onClick={handleUpload}
              disabled={loading}
              className="w-full"
              size="lg"
              data-testid="analyze-button"
            >
              {loading ? "Analiz Ediliyor..." : "Analiz Et"}
            </Button>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Hata</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {result && (
            <Alert className="dark:bg-green-950 dark:border-green-900">
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Başarılı!</AlertTitle>
              <AlertDescription>
                Analiz tamamlandı. Detay sayfasına yönlendiriliyorsunuz...
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {loading && (
        <Card className="dark:bg-gray-900">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                PDF okunuyor ve AI ile analiz ediliyor...
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Geçmiş Analizler Listesi
const CasesList = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const response = await axios.get(`${API}/cases`);
      setCases(response.data);
    } catch (err) {
      console.error("Cases yüklenemedi:", err);
    } finally {
      setLoading(false);
    }
  };

  const getDecisionBadge = (decision) => {
    switch (decision) {
      case "COVERED":
        return <Badge className="bg-green-500">Garanti Kapsamında</Badge>;
      case "OUT_OF_COVERAGE":
        return <Badge variant="destructive">Garanti Dışı</Badge>;
      default:
        return <Badge variant="secondary">Ek Bilgi Gerekli</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 px-4">
      <Card className="dark:bg-gray-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg md:text-xl">
            <List className="w-5 h-5 md:w-6 md:h-6" />
            Geçmiş Analizler
          </CardTitle>
          <CardDescription className="text-sm">
            Tüm IZE analiz sonuçlarını görüntüleyin
          </CardDescription>
        </CardHeader>
        <CardContent>
          {cases.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">Henüz analiz yapılmamış</p>
          ) : (
            <div className="space-y-3">
              {cases.map((caseItem) => (
                <div
                  key={caseItem.id}
                  onClick={() => navigate(`/case/${caseItem.id}`)}
                  className="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors dark:border-gray-700"
                  data-testid={`case-item-${caseItem.id}`}
                >
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                    <div className="flex-1">
                      <h3 className="font-semibold text-base md:text-lg break-words">{caseItem.case_title}</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        IZE No: {caseItem.ize_no} | Firma: {caseItem.company}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        {new Date(caseItem.created_at).toLocaleString('tr-TR')}
                      </p>
                    </div>
                    <div className="self-start">{getDecisionBadge(caseItem.warranty_decision)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Collapsible Section Component
const CollapsibleSection = ({ title, icon, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="w-full">
      <Card className="dark:bg-gray-900 dark:border-gray-700">
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base md:text-lg">
                {icon}
                {title}
              </CardTitle>
              {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0">
            {children}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
};

// Case Detay Sayfası
const CaseDetail = () => {
  const { caseId } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCaseDetail();
  }, [caseId]);

  const fetchCaseDetail = async () => {
    try {
      const response = await axios.get(`${API}/cases/${caseId}`);
      setCaseData(response.data);
    } catch (err) {
      console.error("Case detayı yüklenemedi:", err);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert("Kopyalandı!");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <Alert variant="destructive" className="max-w-4xl mx-auto">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Hata</AlertTitle>
        <AlertDescription>Case bulunamadı</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-4 px-4 pb-8">
      <Card className="dark:bg-gray-900 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="text-lg md:text-xl break-words">{caseData.case_title}</CardTitle>
          <CardDescription className="text-sm">IZE Analiz Sonuçları</CardDescription>
        </CardHeader>
      </Card>

      {/* Özet Bilgiler */}
      <CollapsibleSection title="Özet Bilgiler" icon={<FileText className="w-5 h-5" />} defaultOpen={true}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-semibold">IZE No</Label>
            <p className="text-base md:text-lg">{caseData.ize_no}</p>
          </div>
          <div>
            <Label className="text-sm font-semibold">Firma</Label>
            <p className="text-base md:text-lg break-words">{caseData.company}</p>
          </div>
          <div>
            <Label className="text-sm font-semibold">Plaka</Label>
            <p className="text-base md:text-lg">{caseData.plate}</p>
          </div>
          <div>
            <Label className="text-sm font-semibold">Şasi No</Label>
            <p className="text-base md:text-lg break-all">{caseData.vin}</p>
          </div>
          <div>
            <Label className="text-sm font-semibold">Garanti Başlangıç</Label>
            <p className="text-base md:text-lg">{caseData.warranty_start_date || "Belirtilmemiş"}</p>
          </div>
          <div>
            <Label className="text-sm font-semibold">Araç Yaşı</Label>
            <p className="text-base md:text-lg">{caseData.vehicle_age_months} ay</p>
          </div>
        </div>

        <Separator className="my-4" />

        <div>
          <Label className="text-sm font-semibold">Garanti Değerlendirmesi</Label>
          <div className="mt-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              {caseData.is_within_2_year_warranty ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
              <span className="font-semibold">
                {caseData.is_within_2_year_warranty ? "2 Yıl Garanti İçinde" : "2 Yıl Garanti Dışında"}
              </span>
            </div>
            <p className="text-base md:text-lg font-bold text-primary">{caseData.warranty_decision}</p>
          </div>
        </div>

        <div className="mt-4">
          <Label className="text-sm font-semibold">Karar Gerekçeleri</Label>
          <ul className="list-disc list-inside mt-2 space-y-1">
            {caseData.decision_rationale.map((rationale, idx) => (
              <li key={idx} className="text-sm">{rationale}</li>
            ))}
          </ul>
        </div>
      </CollapsibleSection>

      {/* Analiz Detayları */}
      <CollapsibleSection title="Analiz Detayları" icon={<Settings className="w-5 h-5" />}>
        <div className="space-y-4">
          <div>
            <Label className="text-sm font-semibold">Müşteri Şikayeti</Label>
            <p className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded text-sm">{caseData.failure_complaint}</p>
          </div>

          <div>
            <Label className="text-sm font-semibold">Arıza Nedeni</Label>
            <p className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded text-sm">{caseData.failure_cause}</p>
          </div>

          <div>
            <Label className="text-sm font-semibold">Yapılan İşlemler</Label>
            <ul className="list-disc list-inside mt-2 space-y-1">
              {caseData.operations_performed.map((op, idx) => (
                <li key={idx} className="text-sm">{op}</li>
              ))}
            </ul>
          </div>

          <div>
            <Label className="text-sm font-semibold">Değiştirilen Parçalar</Label>
            <div className="mt-2 space-y-2">
              {caseData.parts_replaced.map((part, idx) => (
                <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-800 rounded">
                  <p className="font-semibold text-sm">{part.partName} (Adet: {part.qty})</p>
                  <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400">{part.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div>
            <Label className="text-sm font-semibold">Tamir Süreci Özeti</Label>
            <p className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded text-sm whitespace-pre-wrap">
              {caseData.repair_process_summary}
            </p>
          </div>
        </div>
      </CollapsibleSection>

      {/* Email Taslağı */}
      <CollapsibleSection title="Email Taslağı" icon={<AlertCircle className="w-5 h-5" />}>
        <div className="space-y-4">
          <div>
            <Label className="text-sm font-semibold">Konu</Label>
            <Input value={caseData.email_subject} readOnly className="mt-2 text-sm" />
          </div>

          <div>
            <Label className="text-sm font-semibold">Email İçeriği</Label>
            <Textarea
              value={caseData.email_body}
              readOnly
              rows={12}
              className="mt-2 font-mono text-xs md:text-sm"
            />
          </div>

          <Button 
            className="w-full" 
            onClick={() => copyToClipboard(caseData.email_body)}
            data-testid="copy-email-button"
          >
            Email'i Kopyala
          </Button>
        </div>
      </CollapsibleSection>

      {/* Ham Veri */}
      <CollapsibleSection title="Ham Veri" icon={<FileText className="w-5 h-5" />}>
        <div className="space-y-4">
          <div>
            <Label className="text-sm font-semibold">PDF Dosya Adı</Label>
            <p className="mt-2 text-sm break-all">{caseData.pdf_file_name}</p>
          </div>

          <div>
            <Label className="text-sm font-semibold">Kullanılan Binder Versiyonu</Label>
            <p className="mt-2 text-sm">{caseData.binder_version_used}</p>
          </div>

          <div>
            <Label className="text-sm font-semibold">Çıkarılan Metin (İlk 2000 karakter)</Label>
            <Textarea
              value={caseData.extracted_text}
              readOnly
              rows={8}
              className="mt-2 font-mono text-xs"
            />
          </div>
        </div>
      </CollapsibleSection>
    </div>
  );
};

// Garanti Kuralları Yönetimi
const WarrantyRules = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newRule, setNewRule] = useState({
    rule_version: "",
    rule_text: "",
    keywords: "",
  });

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await axios.get(`${API}/warranty-rules`);
      setRules(response.data);
    } catch (err) {
      console.error("Kurallar yüklenemedi:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRule = async () => {
    try {
      const ruleData = {
        rule_version: newRule.rule_version,
        rule_text: newRule.rule_text,
        keywords: newRule.keywords.split(",").map((k) => k.trim()).filter((k) => k),
      };

      await axios.post(`${API}/warranty-rules`, ruleData);
      setNewRule({ rule_version: "", rule_text: "", keywords: "" });
      setShowAddForm(false);
      fetchRules();
    } catch (err) {
      console.error("Kural eklenemedi:", err);
    }
  };

  const handleDeleteRule = async (ruleId) => {
    if (window.confirm("Bu kuralı silmek istediğinize emin misiniz?")) {
      try {
        await axios.delete(`${API}/warranty-rules/${ruleId}`);
        fetchRules();
      } catch (err) {
        console.error("Kural silinemedi:", err);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 px-4">
      <Card className="dark:bg-gray-900 dark:border-gray-700">
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2 text-lg md:text-xl">
                <Settings className="w-5 h-5 md:w-6 md:h-6" />
                Garanti Kuralları (Warranty Binder)
              </CardTitle>
              <CardDescription className="text-sm">
                Analiz sırasında kullanılacak garanti değerlendirme kurallarını yönetin
              </CardDescription>
            </div>
            <Button 
              onClick={() => setShowAddForm(!showAddForm)} 
              data-testid="add-rule-button"
              size="sm"
              className="w-full md:w-auto"
            >
              {showAddForm ? "İptal" : "Yeni Kural Ekle"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {showAddForm && (
            <Card className="border-2 border-primary dark:bg-gray-800">
              <CardContent className="pt-6 space-y-4">
                <div>
                  <Label className="text-sm">Kural Versiyonu</Label>
                  <Input
                    placeholder="Örn: 1.0"
                    value={newRule.rule_version}
                    onChange={(e) => setNewRule({ ...newRule, rule_version: e.target.value })}
                    className="text-sm"
                  />
                </div>
                <div>
                  <Label className="text-sm">Kural Metni</Label>
                  <Textarea
                    placeholder="Garanti kuralını detaylı şekilde yazın..."
                    value={newRule.rule_text}
                    onChange={(e) => setNewRule({ ...newRule, rule_text: e.target.value })}
                    rows={5}
                    className="text-sm"
                  />
                </div>
                <div>
                  <Label className="text-sm">Anahtar Kelimeler (virgülle ayırın)</Label>
                  <Input
                    placeholder="garanti, warranty, 2 yıl, üretim hatası"
                    value={newRule.keywords}
                    onChange={(e) => setNewRule({ ...newRule, keywords: e.target.value })}
                    className="text-sm"
                  />
                </div>
                <Button onClick={handleAddRule} className="w-full" data-testid="save-rule-button">
                  Kuralı Kaydet
                </Button>
              </CardContent>
            </Card>
          )}

          {rules.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">Henüz kural eklenmemiş</p>
          ) : (
            <div className="space-y-3">
              {rules.map((rule) => (
                <Card key={rule.id} className="dark:bg-gray-800 dark:border-gray-700">
                  <CardContent className="pt-6">
                    <div className="flex flex-col gap-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <Badge className="text-xs">Versiyon: {rule.rule_version}</Badge>
                            <span className="text-xs text-gray-400 dark:text-gray-500">
                              {new Date(rule.created_at).toLocaleString('tr-TR')}
                            </span>
                          </div>
                          <p className="text-sm mb-2 whitespace-pre-wrap break-words">{rule.rule_text}</p>
                          <div className="flex flex-wrap gap-1">
                            {rule.keywords.map((keyword, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {keyword}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteRule(rule.id)}
                          className="shrink-0"
                        >
                          Sil
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Layout Bileşeni
const Layout = ({ children }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors">
      <nav className="bg-white dark:bg-gray-900 border-b dark:border-gray-800 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 md:h-16">
            <div className="flex items-center gap-4 md:gap-8 min-w-0">
              <Link to="/" className="flex items-center gap-2 min-w-0">
                <FileText className="w-6 h-6 md:w-8 md:h-8 text-primary shrink-0" />
                <span className="text-base md:text-xl font-bold truncate">IZE Case Resolver</span>
              </Link>
              <div className="hidden sm:flex gap-2">
                <Link to="/">
                  <Button variant="ghost" size="sm" className="flex items-center gap-1 md:gap-2">
                    <Home className="w-4 h-4" />
                    <span className="hidden md:inline">Ana Sayfa</span>
                  </Button>
                </Link>
                <Link to="/cases">
                  <Button variant="ghost" size="sm" className="flex items-center gap-1 md:gap-2">
                    <List className="w-4 h-4" />
                    <span className="hidden md:inline">Analizler</span>
                  </Button>
                </Link>
                <Link to="/rules">
                  <Button variant="ghost" size="sm" className="flex items-center gap-1 md:gap-2">
                    <Settings className="w-4 h-4" />
                    <span className="hidden md:inline">Kurallar</span>
                  </Button>
                </Link>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={toggleTheme}
              className="shrink-0"
              aria-label="Toggle theme"
            >
              {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </Button>
          </div>
        </div>
        
        {/* Mobile Navigation */}
        <div className="sm:hidden border-t dark:border-gray-800 px-4 py-2">
          <div className="flex justify-around">
            <Link to="/">
              <Button variant="ghost" size="sm" className="flex flex-col items-center gap-1 h-auto py-2">
                <Home className="w-4 h-4" />
                <span className="text-xs">Ana Sayfa</span>
              </Button>
            </Link>
            <Link to="/cases">
              <Button variant="ghost" size="sm" className="flex flex-col items-center gap-1 h-auto py-2">
                <List className="w-4 h-4" />
                <span className="text-xs">Analizler</span>
              </Button>
            </Link>
            <Link to="/rules">
              <Button variant="ghost" size="sm" className="flex flex-col items-center gap-1 h-auto py-2">
                <Settings className="w-4 h-4" />
                <span className="text-xs">Kurallar</span>
              </Button>
            </Link>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-4 md:py-8">
        {children}
      </main>
    </div>
  );
};

// Ana App Bileşeni
function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/cases" element={<CasesList />} />
            <Route path="/case/:caseId" element={<CaseDetail />} />
            <Route path="/rules" element={<WarrantyRules />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
