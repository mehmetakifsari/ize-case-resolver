import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
  CreditCard, Save, Loader2, CheckCircle, Eye, EyeOff, Building2, FileText,
  Globe, AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const PaymentSettings = ({ token, language }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  
  // Payment provider settings
  const [paymentSettings, setPaymentSettings] = useState({
    stripe_enabled: true,
    stripe_mode: "test",
    stripe_test_publishable_key: "",
    stripe_test_secret_key: "",
    stripe_live_publishable_key: "",
    stripe_live_secret_key: "",
    iyzico_enabled: true,
    iyzico_mode: "sandbox",
    iyzico_sandbox_api_key: "",
    iyzico_sandbox_secret_key: "",
    iyzico_production_api_key: "",
    iyzico_production_secret_key: "",
    bank_transfer_enabled: true
  });
  
  // Invoice settings
  const [invoiceSettings, setInvoiceSettings] = useState({
    active_provider: "manual",
    auto_generate: true,
    company: {
      company_name: "",
      tax_office: "",
      tax_number: "",
      address: "",
      phone: "",
      email: "",
      website: ""
    },
    parasut_enabled: false,
    parasut_client_id: "",
    parasut_client_secret: "",
    parasut_company_id: "",
    bizimhesap_enabled: false,
    bizimhesap_api_key: "",
    bizimhesap_secret_key: "",
    birfatura_enabled: false,
    birfatura_api_key: "",
    birfatura_username: "",
    birfatura_password: "",
    invoice_prefix: "IZE"
  });
  
  const [showSecrets, setShowSecrets] = useState({});

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const [paymentRes, invoiceRes] = await Promise.all([
        axios.get(`${API}/settings/payment-providers`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/settings/invoice`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setPaymentSettings(paymentRes.data);
      setInvoiceSettings(invoiceRes.data);
    } catch (error) {
      console.error("Settings fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const savePaymentSettings = async () => {
    try {
      setSaving(true);
      await axios.put(`${API}/settings/payment-providers`, paymentSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessage({ type: "success", text: language === "tr" ? "Ödeme ayarları kaydedildi" : "Payment settings saved" });
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Hata oluştu" });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage({ type: "", text: "" }), 3000);
    }
  };

  const saveInvoiceSettings = async () => {
    try {
      setSaving(true);
      await axios.put(`${API}/settings/invoice`, invoiceSettings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessage({ type: "success", text: language === "tr" ? "Fatura ayarları kaydedildi" : "Invoice settings saved" });
    } catch (error) {
      setMessage({ type: "error", text: error.response?.data?.detail || "Hata oluştu" });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage({ type: "", text: "" }), 3000);
    }
  };

  const toggleShowSecret = (field) => {
    setShowSecrets(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const SecretInput = ({ field, value, onChange, placeholder }) => (
    <div className="relative">
      <Input
        type={showSecrets[field] ? "text" : "password"}
        value={value || ""}
        onChange={onChange}
        placeholder={placeholder}
        className="pr-10"
      />
      <button
        type="button"
        onClick={() => toggleShowSecret(field)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
      >
        {showSecrets[field] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {message.text && (
        <Alert variant={message.type === "error" ? "destructive" : "default"}>
          {message.type === "success" ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="payment" className="space-y-6">
        <TabsList className="grid w-full max-w-lg grid-cols-2">
          <TabsTrigger value="payment" className="flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            {language === "tr" ? "Ödeme Sağlayıcılar" : "Payment Providers"}
          </TabsTrigger>
          <TabsTrigger value="invoice" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            {language === "tr" ? "Fatura Ayarları" : "Invoice Settings"}
          </TabsTrigger>
        </TabsList>

        {/* Ödeme Sağlayıcılar */}
        <TabsContent value="payment" className="space-y-6">
          {/* Stripe */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-8 bg-[#635BFF] rounded flex items-center justify-center">
                    <span className="text-white font-bold text-xs">Stripe</span>
                  </div>
                  <div>
                    <CardTitle className="text-lg">Stripe</CardTitle>
                    <CardDescription>{language === "tr" ? "Uluslararası kartlar için" : "For international cards"}</CardDescription>
                  </div>
                </div>
                <Switch
                  checked={paymentSettings.stripe_enabled}
                  onCheckedChange={(checked) => setPaymentSettings(p => ({ ...p, stripe_enabled: checked }))}
                />
              </div>
            </CardHeader>
            {paymentSettings.stripe_enabled && (
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label>{language === "tr" ? "Mod" : "Mode"}</Label>
                    <Select
                      value={paymentSettings.stripe_mode}
                      onValueChange={(v) => setPaymentSettings(p => ({ ...p, stripe_mode: v }))}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="test">Test</SelectItem>
                        <SelectItem value="live">Live (Production)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {paymentSettings.stripe_mode === "test" ? (
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label>Test Publishable Key</Label>
                      <Input
                        value={paymentSettings.stripe_test_publishable_key || ""}
                        onChange={(e) => setPaymentSettings(p => ({ ...p, stripe_test_publishable_key: e.target.value }))}
                        placeholder="pk_test_..."
                      />
                    </div>
                    <div>
                      <Label>Test Secret Key</Label>
                      <SecretInput
                        field="stripe_test_secret"
                        value={paymentSettings.stripe_test_secret_key}
                        onChange={(e) => setPaymentSettings(p => ({ ...p, stripe_test_secret_key: e.target.value }))}
                        placeholder="sk_test_..."
                      />
                    </div>
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label>Live Publishable Key</Label>
                      <Input
                        value={paymentSettings.stripe_live_publishable_key || ""}
                        onChange={(e) => setPaymentSettings(p => ({ ...p, stripe_live_publishable_key: e.target.value }))}
                        placeholder="pk_live_..."
                      />
                    </div>
                    <div>
                      <Label>Live Secret Key</Label>
                      <SecretInput
                        field="stripe_live_secret"
                        value={paymentSettings.stripe_live_secret_key}
                        onChange={(e) => setPaymentSettings(p => ({ ...p, stripe_live_secret_key: e.target.value }))}
                        placeholder="sk_live_..."
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            )}
          </Card>

          {/* iyzico */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-8 bg-[#1E3A5F] rounded flex items-center justify-center">
                    <span className="text-white font-bold text-xs">iyzico</span>
                  </div>
                  <div>
                    <CardTitle className="text-lg">iyzico</CardTitle>
                    <CardDescription>{language === "tr" ? "Türk kartları için" : "For Turkish cards"}</CardDescription>
                  </div>
                </div>
                <Switch
                  checked={paymentSettings.iyzico_enabled}
                  onCheckedChange={(checked) => setPaymentSettings(p => ({ ...p, iyzico_enabled: checked }))}
                />
              </div>
            </CardHeader>
            {paymentSettings.iyzico_enabled && (
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label>{language === "tr" ? "Mod" : "Mode"}</Label>
                    <Select
                      value={paymentSettings.iyzico_mode}
                      onValueChange={(v) => setPaymentSettings(p => ({ ...p, iyzico_mode: v }))}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sandbox">Sandbox (Test)</SelectItem>
                        <SelectItem value="production">Production</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {paymentSettings.iyzico_mode === "sandbox" ? (
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label>Sandbox API Key</Label>
                      <Input
                        value={paymentSettings.iyzico_sandbox_api_key || ""}
                        onChange={(e) => setPaymentSettings(p => ({ ...p, iyzico_sandbox_api_key: e.target.value }))}
                        placeholder="sandbox-..."
                      />
                    </div>
                    <div>
                      <Label>Sandbox Secret Key</Label>
                      <SecretInput
                        field="iyzico_sandbox_secret"
                        value={paymentSettings.iyzico_sandbox_secret_key}
                        onChange={(e) => setPaymentSettings(p => ({ ...p, iyzico_sandbox_secret_key: e.target.value }))}
                        placeholder="sandbox-..."
                      />
                    </div>
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label>Production API Key</Label>
                      <Input
                        value={paymentSettings.iyzico_production_api_key || ""}
                        onChange={(e) => setPaymentSettings(p => ({ ...p, iyzico_production_api_key: e.target.value }))}
                        placeholder="..."
                      />
                    </div>
                    <div>
                      <Label>Production Secret Key</Label>
                      <SecretInput
                        field="iyzico_prod_secret"
                        value={paymentSettings.iyzico_production_secret_key}
                        onChange={(e) => setPaymentSettings(p => ({ ...p, iyzico_production_secret_key: e.target.value }))}
                        placeholder="..."
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            )}
          </Card>

          {/* Havale/EFT */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-8 bg-gray-700 rounded flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{language === "tr" ? "Havale / EFT" : "Bank Transfer"}</CardTitle>
                    <CardDescription>{language === "tr" ? "Manuel onay gerektirir" : "Requires manual approval"}</CardDescription>
                  </div>
                </div>
                <Switch
                  checked={paymentSettings.bank_transfer_enabled}
                  onCheckedChange={(checked) => setPaymentSettings(p => ({ ...p, bank_transfer_enabled: checked }))}
                />
              </div>
            </CardHeader>
          </Card>

          <Button onClick={savePaymentSettings} disabled={saving} className="w-full md:w-auto">
            {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
            {language === "tr" ? "Ödeme Ayarlarını Kaydet" : "Save Payment Settings"}
          </Button>
        </TabsContent>

        {/* Fatura Ayarları */}
        <TabsContent value="invoice" className="space-y-6">
          {/* Şirket Bilgileri */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5" />
                {language === "tr" ? "Şirket Bilgileri" : "Company Information"}
              </CardTitle>
              <CardDescription>
                {language === "tr" ? "Faturalarda görünecek şirket bilgileri" : "Company info displayed on invoices"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>{language === "tr" ? "Şirket Adı" : "Company Name"}</Label>
                  <Input
                    value={invoiceSettings.company?.company_name || ""}
                    onChange={(e) => setInvoiceSettings(p => ({ 
                      ...p, 
                      company: { ...p.company, company_name: e.target.value }
                    }))}
                    placeholder="IZE Case Resolver Ltd. Şti."
                  />
                </div>
                <div>
                  <Label>{language === "tr" ? "Vergi Dairesi" : "Tax Office"}</Label>
                  <Input
                    value={invoiceSettings.company?.tax_office || ""}
                    onChange={(e) => setInvoiceSettings(p => ({ 
                      ...p, 
                      company: { ...p.company, tax_office: e.target.value }
                    }))}
                    placeholder="Nilüfer Vergi Dairesi"
                  />
                </div>
                <div>
                  <Label>{language === "tr" ? "Vergi Numarası" : "Tax Number"}</Label>
                  <Input
                    value={invoiceSettings.company?.tax_number || ""}
                    onChange={(e) => setInvoiceSettings(p => ({ 
                      ...p, 
                      company: { ...p.company, tax_number: e.target.value }
                    }))}
                    placeholder="1234567890"
                  />
                </div>
                <div>
                  <Label>{language === "tr" ? "Telefon" : "Phone"}</Label>
                  <Input
                    value={invoiceSettings.company?.phone || ""}
                    onChange={(e) => setInvoiceSettings(p => ({ 
                      ...p, 
                      company: { ...p.company, phone: e.target.value }
                    }))}
                    placeholder="+90 224 123 45 67"
                  />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input
                    value={invoiceSettings.company?.email || ""}
                    onChange={(e) => setInvoiceSettings(p => ({ 
                      ...p, 
                      company: { ...p.company, email: e.target.value }
                    }))}
                    placeholder="info@izeresolver.com"
                  />
                </div>
                <div>
                  <Label>Website</Label>
                  <Input
                    value={invoiceSettings.company?.website || ""}
                    onChange={(e) => setInvoiceSettings(p => ({ 
                      ...p, 
                      company: { ...p.company, website: e.target.value }
                    }))}
                    placeholder="https://izeresolver.com"
                  />
                </div>
              </div>
              <div>
                <Label>{language === "tr" ? "Adres" : "Address"}</Label>
                <Textarea
                  value={invoiceSettings.company?.address || ""}
                  onChange={(e) => setInvoiceSettings(p => ({ 
                    ...p, 
                    company: { ...p.company, address: e.target.value }
                  }))}
                  placeholder="Nilüfer, Bursa, Türkiye"
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>

          {/* Fatura Sağlayıcıları */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                {language === "tr" ? "E-Fatura Entegrasyonu" : "E-Invoice Integration"}
              </CardTitle>
              <CardDescription>
                {language === "tr" ? "Aktif edilip yapılandırılan sistem kullanılır" : "The active and configured system will be used"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label>{language === "tr" ? "Aktif Sağlayıcı" : "Active Provider"}</Label>
                  <Select
                    value={invoiceSettings.active_provider}
                    onValueChange={(v) => setInvoiceSettings(p => ({ ...p, active_provider: v }))}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="manual">{language === "tr" ? "Manuel (PDF)" : "Manual (PDF)"}</SelectItem>
                      <SelectItem value="parasut">Paraşüt</SelectItem>
                      <SelectItem value="bizimhesap">Bizimhesap</SelectItem>
                      <SelectItem value="birfatura">Birfatura</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>{language === "tr" ? "Fatura Prefix" : "Invoice Prefix"}</Label>
                  <Input
                    value={invoiceSettings.invoice_prefix || ""}
                    onChange={(e) => setInvoiceSettings(p => ({ ...p, invoice_prefix: e.target.value }))}
                    placeholder="IZE"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Switch
                  checked={invoiceSettings.auto_generate}
                  onCheckedChange={(checked) => setInvoiceSettings(p => ({ ...p, auto_generate: checked }))}
                />
                <Label>{language === "tr" ? "Ödeme sonrası otomatik fatura oluştur" : "Auto-generate invoice after payment"}</Label>
              </div>

              {/* Paraşüt */}
              <div className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Paraşüt</span>
                  <Switch
                    checked={invoiceSettings.parasut_enabled}
                    onCheckedChange={(checked) => setInvoiceSettings(p => ({ ...p, parasut_enabled: checked }))}
                  />
                </div>
                {invoiceSettings.parasut_enabled && (
                  <div className="grid md:grid-cols-3 gap-3">
                    <div>
                      <Label className="text-sm">Client ID</Label>
                      <Input
                        value={invoiceSettings.parasut_client_id || ""}
                        onChange={(e) => setInvoiceSettings(p => ({ ...p, parasut_client_id: e.target.value }))}
                        placeholder="Client ID"
                      />
                    </div>
                    <div>
                      <Label className="text-sm">Client Secret</Label>
                      <SecretInput
                        field="parasut_secret"
                        value={invoiceSettings.parasut_client_secret}
                        onChange={(e) => setInvoiceSettings(p => ({ ...p, parasut_client_secret: e.target.value }))}
                        placeholder="Client Secret"
                      />
                    </div>
                    <div>
                      <Label className="text-sm">Company ID</Label>
                      <Input
                        value={invoiceSettings.parasut_company_id || ""}
                        onChange={(e) => setInvoiceSettings(p => ({ ...p, parasut_company_id: e.target.value }))}
                        placeholder="Company ID"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Bizimhesap */}
              <div className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Bizimhesap</span>
                  <Switch
                    checked={invoiceSettings.bizimhesap_enabled}
                    onCheckedChange={(checked) => setInvoiceSettings(p => ({ ...p, bizimhesap_enabled: checked }))}
                  />
                </div>
                {invoiceSettings.bizimhesap_enabled && (
                  <div className="grid md:grid-cols-2 gap-3">
                    <div>
                      <Label className="text-sm">API Key</Label>
                      <Input
                        value={invoiceSettings.bizimhesap_api_key || ""}
                        onChange={(e) => setInvoiceSettings(p => ({ ...p, bizimhesap_api_key: e.target.value }))}
                        placeholder="API Key"
                      />
                    </div>
                    <div>
                      <Label className="text-sm">Secret Key</Label>
                      <SecretInput
                        field="bizimhesap_secret"
                        value={invoiceSettings.bizimhesap_secret_key}
                        onChange={(e) => setInvoiceSettings(p => ({ ...p, bizimhesap_secret_key: e.target.value }))}
                        placeholder="Secret Key"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Birfatura */}
              <div className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">Birfatura</span>
                  <Switch
                    checked={invoiceSettings.birfatura_enabled}
                    onCheckedChange={(checked) => setInvoiceSettings(p => ({ ...p, birfatura_enabled: checked }))}
                  />
                </div>
                {invoiceSettings.birfatura_enabled && (
                  <div className="grid md:grid-cols-3 gap-3">
                    <div>
                      <Label className="text-sm">API Key</Label>
                      <Input
                        value={invoiceSettings.birfatura_api_key || ""}
                        onChange={(e) => setInvoiceSettings(p => ({ ...p, birfatura_api_key: e.target.value }))}
                        placeholder="API Key"
                      />
                    </div>
                    <div>
                      <Label className="text-sm">{language === "tr" ? "Kullanıcı Adı" : "Username"}</Label>
                      <Input
                        value={invoiceSettings.birfatura_username || ""}
                        onChange={(e) => setInvoiceSettings(p => ({ ...p, birfatura_username: e.target.value }))}
                        placeholder="Username"
                      />
                    </div>
                    <div>
                      <Label className="text-sm">{language === "tr" ? "Şifre" : "Password"}</Label>
                      <SecretInput
                        field="birfatura_password"
                        value={invoiceSettings.birfatura_password}
                        onChange={(e) => setInvoiceSettings(p => ({ ...p, birfatura_password: e.target.value }))}
                        placeholder="Password"
                      />
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Button onClick={saveInvoiceSettings} disabled={saving} className="w-full md:w-auto">
            {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
            {language === "tr" ? "Fatura Ayarlarını Kaydet" : "Save Invoice Settings"}
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PaymentSettings;
