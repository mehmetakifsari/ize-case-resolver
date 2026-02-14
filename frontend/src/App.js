import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, List, Settings, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
    <div className="max-w-4xl mx-auto space-y-6">
      <Card className="border-2 border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-6 h-6" />
            IZE Dosyası Yükle ve Analiz Et
          </CardTitle>
          <CardDescription>
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
            <label
              htmlFor="pdf-upload"
              className="flex-1 cursor-pointer"
            >
              <div className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary transition-colors">
                <FileText className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p className="text-sm text-gray-600">
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
            <Alert>
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
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="text-sm text-gray-600">PDF okunuyor ve AI ile analiz ediliyor...</p>
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
    <div className="max-w-6xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <List className="w-6 h-6" />
            Geçmiş Analizler
          </CardTitle>
          <CardDescription>
            Tüm IZE analiz sonuçlarını görüntüleyin
          </CardDescription>
        </CardHeader>
        <CardContent>
          {cases.length === 0 ? (
            <p className="text-center text-gray-500 py-8">Henüz analiz yapılmamış</p>
          ) : (
            <div className="space-y-3">
              {cases.map((caseItem) => (
                <div
                  key={caseItem.id}
                  onClick={() => navigate(`/case/${caseItem.id}`)}
                  className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  data-testid={`case-item-${caseItem.id}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{caseItem.case_title}</h3>
                      <p className="text-sm text-gray-500">IZE No: {caseItem.ize_no} | Firma: {caseItem.company}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(caseItem.created_at).toLocaleString('tr-TR')}
                      </p>
                    </div>
                    <div>{getDecisionBadge(caseItem.warranty_decision)}</div>
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

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Hata</AlertTitle>
        <AlertDescription>Case bulunamadı</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{caseData.case_title}</CardTitle>
          <CardDescription>IZE Analiz Sonuçları</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="summary" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="summary">Özet</TabsTrigger>
              <TabsTrigger value="analysis">Analiz Detayları</TabsTrigger>
              <TabsTrigger value="email">Email Taslağı</TabsTrigger>
              <TabsTrigger value="raw">Ham Veri</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-semibold">IZE No</Label>
                  <p className="text-lg">{caseData.ize_no}</p>
                </div>
                <div>
                  <Label className="text-sm font-semibold">Firma</Label>
                  <p className="text-lg">{caseData.company}</p>
                </div>
                <div>
                  <Label className="text-sm font-semibold">Plaka</Label>
                  <p className="text-lg">{caseData.plate}</p>
                </div>
                <div>
                  <Label className="text-sm font-semibold">Şasi No</Label>
                  <p className="text-lg">{caseData.vin}</p>
                </div>
                <div>
                  <Label className="text-sm font-semibold">Garanti Başlangıç</Label>
                  <p className="text-lg">{caseData.warranty_start_date || "Belirtilmemiş"}</p>
                </div>
                <div>
                  <Label className="text-sm font-semibold">Araç Yaşı</Label>
                  <p className="text-lg">{caseData.vehicle_age_months} ay</p>
                </div>
              </div>

              <Separator />

              <div>
                <Label className="text-sm font-semibold">Garanti Değerlendirmesi</Label>
                <div className="mt-2 p-4 bg-gray-50 rounded-lg">
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
                  <p className="text-lg font-bold text-primary">{caseData.warranty_decision}</p>
                </div>
              </div>

              <div>
                <Label className="text-sm font-semibold">Karar Gerekçeleri</Label>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  {caseData.decision_rationale.map((rationale, idx) => (
                    <li key={idx} className="text-sm">{rationale}</li>
                  ))}
                </ul>
              </div>
            </TabsContent>

            <TabsContent value="analysis" className="space-y-4">
              <div>
                <Label className="text-sm font-semibold">Müşteri Şikayeti</Label>
                <p className="mt-2 p-3 bg-gray-50 rounded">{caseData.failure_complaint}</p>
              </div>

              <div>
                <Label className="text-sm font-semibold">Arıza Nedeni</Label>
                <p className="mt-2 p-3 bg-gray-50 rounded">{caseData.failure_cause}</p>
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
                    <div key={idx} className="p-3 bg-gray-50 rounded">
                      <p className="font-semibold">{part.partName} (Adet: {part.qty})</p>
                      <p className="text-sm text-gray-600">{part.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-sm font-semibold">Tamir Süreci Özeti</Label>
                <p className="mt-2 p-3 bg-gray-50 rounded whitespace-pre-wrap">{caseData.repair_process_summary}</p>
              </div>
            </TabsContent>

            <TabsContent value="email" className="space-y-4">
              <div>
                <Label className="text-sm font-semibold">Konu</Label>
                <Input value={caseData.email_subject} readOnly className="mt-2" />
              </div>

              <div>
                <Label className="text-sm font-semibold">Email İçeriği</Label>
                <Textarea
                  value={caseData.email_body}
                  readOnly
                  rows={15}
                  className="mt-2 font-mono text-sm"
                />
              </div>

              <Button className="w-full" data-testid="copy-email-button">
                Email'i Kopyala
              </Button>
            </TabsContent>

            <TabsContent value="raw" className="space-y-4">
              <div>
                <Label className="text-sm font-semibold">PDF Dosya Adı</Label>
                <p className="mt-2">{caseData.pdf_file_name}</p>
              </div>

              <div>
                <Label className="text-sm font-semibold">Kullanılan Binder Versiyonu</Label>
                <p className="mt-2">{caseData.binder_version_used}</p>
              </div>

              <div>
                <Label className="text-sm font-semibold">Çıkarılan Metin (İlk 2000 karakter)</Label>
                <Textarea
                  value={caseData.extracted_text}
                  readOnly
                  rows={10}
                  className="mt-2 font-mono text-xs"
                />
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
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
    <div className="max-w-6xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-6 h-6" />
                Garanti Kuralları (Warranty Binder)
              </CardTitle>
              <CardDescription>
                Analiz sırasında kullanılacak garanti değerlendirme kurallarını yönetin
              </CardDescription>
            </div>
            <Button onClick={() => setShowAddForm(!showAddForm)} data-testid="add-rule-button">
              {showAddForm ? "İptal" : "Yeni Kural Ekle"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {showAddForm && (
            <Card className="border-2 border-primary">
              <CardContent className="pt-6 space-y-4">
                <div>
                  <Label>Kural Versiyonu</Label>
                  <Input
                    placeholder="Örn: 1.0"
                    value={newRule.rule_version}
                    onChange={(e) => setNewRule({ ...newRule, rule_version: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Kural Metni</Label>
                  <Textarea
                    placeholder="Garanti kuralını detaylı şekilde yazın..."
                    value={newRule.rule_text}
                    onChange={(e) => setNewRule({ ...newRule, rule_text: e.target.value })}
                    rows={5}
                  />
                </div>
                <div>
                  <Label>Anahtar Kelimeler (virgülle ayırın)</Label>
                  <Input
                    placeholder="garanti, warranty, 2 yıl, üretim hatası"
                    value={newRule.keywords}
                    onChange={(e) => setNewRule({ ...newRule, keywords: e.target.value })}
                  />
                </div>
                <Button onClick={handleAddRule} className="w-full" data-testid="save-rule-button">
                  Kuralı Kaydet
                </Button>
              </CardContent>
            </Card>
          )}

          {rules.length === 0 ? (
            <p className="text-center text-gray-500 py-8">Henüz kural eklenmemiş</p>
          ) : (
            <div className="space-y-3">
              {rules.map((rule) => (
                <Card key={rule.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge>Versiyon: {rule.rule_version}</Badge>
                          <span className="text-xs text-gray-400">
                            {new Date(rule.created_at).toLocaleString('tr-TR')}
                          </span>
                        </div>
                        <p className="text-sm mb-2 whitespace-pre-wrap">{rule.rule_text}</p>
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
                      >
                        Sil
                      </Button>
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
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2">
                <FileText className="w-8 h-8 text-primary" />
                <span className="text-xl font-bold">IZE Case Resolver</span>
              </Link>
              <div className="hidden md:flex gap-4">
                <Link to="/">
                  <Button variant="ghost" className="flex items-center gap-2">
                    <Home className="w-4 h-4" />
                    Ana Sayfa
                  </Button>
                </Link>
                <Link to="/cases">
                  <Button variant="ghost" className="flex items-center gap-2">
                    <List className="w-4 h-4" />
                    Geçmiş Analizler
                  </Button>
                </Link>
                <Link to="/rules">
                  <Button variant="ghost" className="flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Garanti Kuralları
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};

// Ana App Bileşeni
function App() {
  return (
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
  );
}

export default App;
