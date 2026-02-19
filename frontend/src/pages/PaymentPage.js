import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { 
  CreditCard, CheckCircle, XCircle, Loader2, Building2, ArrowLeft,
  Zap, Shield, Crown, Banknote, Copy, Check
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ==================== ÖDEME SAYFASI ====================

export const PaymentPage = ({ user, token, t, language }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [activeTab, setActiveTab] = useState("credits");
  const [creditPackages, setCreditPackages] = useState([]);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [bankAccounts, setBankAccounts] = useState({ accounts: [], instructions: "" });
  
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [selectedCurrency, setSelectedCurrency] = useState("TRY");
  const [paymentMethod, setPaymentMethod] = useState("stripe");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Banka transferi için
  const [bankReference, setBankReference] = useState("");
  const [copiedIban, setCopiedIban] = useState(null);

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    try {
      // Yeni public pricing-plans endpoint'inden çek
      const [pricingRes, bankRes] = await Promise.all([
        axios.get(`${API}/settings/public/pricing-plans`),
        axios.get(`${API}/payments/bank-accounts`).catch(() => ({ data: { accounts: [], instructions: "" } }))
      ]);
      
      // Plan tipine göre ayır
      const allPlans = pricingRes.data || [];
      const credits = allPlans.filter(p => p.plan_type === "package");
      const subs = allPlans.filter(p => p.plan_type === "subscription");
      
      // Eski format uyumluluğu için dönüştür
      const formattedCredits = credits.map(p => ({
        ...p,
        price_try: p.currency === "TRY" ? p.price : p.price * 30,
        price_usd: p.currency === "USD" ? p.price : p.price / 30,
        price_eur: p.currency === "EUR" ? p.price : p.price / 35,
      }));
      
      const formattedSubs = subs.map(p => ({
        ...p,
        price_try: p.currency === "TRY" ? p.price : p.price * 30,
        price_usd: p.currency === "USD" ? p.price : p.price / 30,
        price_eur: p.currency === "EUR" ? p.price : p.price / 35,
      }));
      
      setCreditPackages(formattedCredits);
      setSubscriptionPlans(formattedSubs);
      setBankAccounts(bankRes.data);
    } catch (err) {
      console.error("Paketler yüklenemedi:", err);
      // Varsayılan paketler
      setCreditPackages([
        { id: "starter", name: "Başlangıç", credits: 10, price_try: 100, price_usd: 10, price_eur: 9, features: ["10 IZE Analizi", "E-posta Desteği"] },
        { id: "pro", name: "Pro", credits: 50, price_try: 400, price_usd: 40, price_eur: 35, is_popular: true, features: ["50 IZE Analizi", "Öncelikli Destek"] },
        { id: "enterprise", name: "Enterprise", credits: 200, price_try: 1200, price_usd: 120, price_eur: 105, features: ["200 IZE Analizi", "7/24 Destek"] }
      ]);
    }
  };

  const getPrice = (pkg) => {
    const key = `price_${selectedCurrency.toLowerCase()}`;
    return pkg[key] || pkg.price || 0;
  };

  const formatPrice = (amount) => {
    const symbols = { TRY: "₺", USD: "$", EUR: "€" };
    return `${symbols[selectedCurrency]}${Number(amount).toFixed(2)}`;
  };

  const handleCheckout = async () => {
    if (!selectedPackage) {
      setError(language === "tr" ? "Lütfen bir paket seçin" : "Please select a package");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const packageType = activeTab === "credits" ? "credit" : "subscription";
      const originUrl = window.location.origin;

      if (paymentMethod === "bank_transfer") {
        // Havale/EFT
        if (!bankReference.trim()) {
          setError(language === "tr" ? "Lütfen referans numarasını girin" : "Please enter reference number");
          setLoading(false);
          return;
        }

        const response = await axios.post(
          `${API}/payments/checkout/bank-transfer`,
          {
            package_type: packageType,
            package_id: selectedPackage.id,
            currency: selectedCurrency,
            bank_account_id: bankAccounts.accounts.find(a => a.currency === selectedCurrency)?.id || "bank_try",
            transfer_reference: bankReference
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        if (response.data.success) {
          navigate(`/payment/pending?transaction_id=${response.data.transaction_id}`);
        }
      } else {
        // Stripe veya iyzico
        const endpoint = paymentMethod === "stripe" 
          ? `${API}/payments/checkout/stripe`
          : `${API}/payments/checkout/iyzico`;

        const response = await axios.post(
          endpoint,
          {
            package_type: packageType,
            package_id: selectedPackage.id,
            payment_method: paymentMethod,
            currency: selectedCurrency,
            origin_url: originUrl
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        if (response.data.success && response.data.checkout_url) {
          window.location.href = response.data.checkout_url;
        } else if (response.data.message && paymentMethod === "iyzico") {
          // iyzico checkout form HTML'i
          const newWindow = window.open("", "_self");
          newWindow.document.write(response.data.message);
        }
      }
    } catch (err) {
      console.error("Checkout error:", err);
      setError(err.response?.data?.detail || (language === "tr" ? "Bir hata oluştu" : "An error occurred"));
    } finally {
      setLoading(false);
    }
  };

  const copyIban = (iban, id) => {
    navigator.clipboard.writeText(iban);
    setCopiedIban(id);
    setTimeout(() => setCopiedIban(null), 2000);
  };

  const PackageCard = ({ pkg, isSelected, onSelect, type }) => {
    const price = getPrice(pkg);
    const name = language === "en" && pkg.name_en ? pkg.name_en : pkg.name;
    const description = language === "en" && pkg.description_en ? pkg.description_en : pkg.description;
    
    return (
      <Card 
        className={`cursor-pointer transition-all hover:shadow-lg ${
          isSelected ? "ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-950" : ""
        } ${pkg.is_popular ? "border-blue-500" : ""}`}
        onClick={() => onSelect(pkg)}
        data-testid={`package-card-${pkg.id}`}
      >
        {pkg.is_popular && (
          <div className="absolute -top-3 left-1/2 -translate-x-1/2">
            <Badge className="bg-blue-500">{language === "tr" ? "Popüler" : "Popular"}</Badge>
          </div>
        )}
        <CardHeader className="text-center pb-2">
          <div className="mx-auto mb-2">
            {type === "credit" ? (
              <Zap className={`h-8 w-8 ${pkg.is_popular ? "text-blue-500" : "text-gray-500"}`} />
            ) : (
              <Crown className={`h-8 w-8 ${pkg.is_popular ? "text-blue-500" : "text-gray-500"}`} />
            )}
          </div>
          <CardTitle className="text-lg">{name}</CardTitle>
          <CardDescription className="text-sm">{description}</CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <div className="text-3xl font-bold mb-2">
            {formatPrice(price)}
            {type === "subscription" && (
              <span className="text-sm font-normal text-muted-foreground">
                /{pkg.billing_period === "yearly" ? (language === "tr" ? "yıl" : "yr") : (language === "tr" ? "ay" : "mo")}
              </span>
            )}
          </div>
          {pkg.discount_percent > 0 && (
            <Badge variant="secondary" className="mb-2">
              %{pkg.discount_percent} {language === "tr" ? "indirim" : "off"}
            </Badge>
          )}
          <div className="text-sm text-muted-foreground">
            {type === "credit" ? (
              <span>{pkg.credits} {language === "tr" ? "analiz kredisi" : "analysis credits"}</span>
            ) : (
              <span>{pkg.credits_per_month || pkg.credits} {language === "tr" ? "dönem analizi" : "period analyses"}</span>
            )}
          </div>
          {type === "subscription" && pkg.features && (
            <ul className="mt-4 text-sm text-left space-y-1">
              {(language === "en" && pkg.features_en?.length ? pkg.features_en : pkg.features).map((f, i) => (
                <li key={i} className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
        {isSelected && (
          <CardFooter className="justify-center">
            <Badge variant="default" className="bg-blue-500">
              <CheckCircle className="h-4 w-4 mr-1" />
              {language === "tr" ? "Seçildi" : "Selected"}
            </Badge>
          </CardFooter>
        )}
      </Card>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Button variant="ghost" onClick={() => navigate(-1)} data-testid="back-button">
            <ArrowLeft className="h-4 w-4 mr-2" />
            {language === "tr" ? "Geri" : "Back"}
          </Button>
          <h1 className="text-2xl font-bold">
            {language === "tr" ? "Kredi Satın Al" : "Buy Credits"}
          </h1>
          <div className="w-20" />
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6" data-testid="payment-error">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Para Birimi Seçimi */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            {["TRY", "USD", "EUR"].map((currency) => (
              <button
                key={currency}
                onClick={() => setSelectedCurrency(currency)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedCurrency === currency
                    ? "bg-white dark:bg-gray-700 shadow"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                }`}
                data-testid={`currency-${currency}`}
              >
                {currency === "TRY" ? "₺ TL" : currency === "USD" ? "$ USD" : "€ EUR"}
              </button>
            ))}
          </div>
        </div>

        {/* Paket Tipleri */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-8">
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-2">
            <TabsTrigger value="credits" data-testid="tab-credits">
              <Zap className="h-4 w-4 mr-2" />
              {language === "tr" ? "Kredi Paketi" : "Credit Package"}
            </TabsTrigger>
            <TabsTrigger value="subscription" data-testid="tab-subscription">
              <Crown className="h-4 w-4 mr-2" />
              {language === "tr" ? "Abonelik" : "Subscription"}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="credits" className="mt-6">
            <div className="grid md:grid-cols-3 gap-6">
              {creditPackages.map((pkg) => (
                <PackageCard
                  key={pkg.id}
                  pkg={pkg}
                  type="credit"
                  isSelected={selectedPackage?.id === pkg.id}
                  onSelect={setSelectedPackage}
                />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="subscription" className="mt-6">
            <div className="grid md:grid-cols-3 gap-6">
              {subscriptionPlans.map((plan) => (
                <PackageCard
                  key={plan.id}
                  pkg={plan}
                  type="subscription"
                  isSelected={selectedPackage?.id === plan.id}
                  onSelect={setSelectedPackage}
                />
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {/* Ödeme Yöntemi */}
        {selectedPackage && (
          <Card className="max-w-2xl mx-auto" data-testid="payment-method-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                {language === "tr" ? "Ödeme Yöntemi" : "Payment Method"}
              </CardTitle>
              <CardDescription>
                {language === "tr" 
                  ? "Tercih ettiğiniz ödeme yöntemini seçin"
                  : "Select your preferred payment method"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <RadioGroup value={paymentMethod} onValueChange={setPaymentMethod}>
                {/* Stripe */}
                <div className="flex items-center space-x-3 p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer">
                  <RadioGroupItem value="stripe" id="stripe" data-testid="payment-stripe" />
                  <Label htmlFor="stripe" className="flex items-center gap-3 cursor-pointer flex-1">
                    <div className="w-12 h-8 bg-[#635BFF] rounded flex items-center justify-center">
                      <span className="text-white font-bold text-xs">Stripe</span>
                    </div>
                    <div>
                      <p className="font-medium">{language === "tr" ? "Kredi/Banka Kartı" : "Credit/Debit Card"}</p>
                      <p className="text-sm text-muted-foreground">Visa, Mastercard, Amex</p>
                    </div>
                  </Label>
                  <Shield className="h-5 w-5 text-green-500" />
                </div>

                {/* iyzico */}
                <div className="flex items-center space-x-3 p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer">
                  <RadioGroupItem value="iyzico" id="iyzico" data-testid="payment-iyzico" />
                  <Label htmlFor="iyzico" className="flex items-center gap-3 cursor-pointer flex-1">
                    <div className="w-12 h-8 bg-[#1E3A5F] rounded flex items-center justify-center">
                      <span className="text-white font-bold text-xs">iyzico</span>
                    </div>
                    <div>
                      <p className="font-medium">iyzico</p>
                      <p className="text-sm text-muted-foreground">
                        {language === "tr" ? "Türk kartları için" : "For Turkish cards"}
                      </p>
                    </div>
                  </Label>
                  <Shield className="h-5 w-5 text-green-500" />
                </div>

                {/* Havale/EFT */}
                <div className="flex items-center space-x-3 p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer">
                  <RadioGroupItem value="bank_transfer" id="bank_transfer" data-testid="payment-bank" />
                  <Label htmlFor="bank_transfer" className="flex items-center gap-3 cursor-pointer flex-1">
                    <div className="w-12 h-8 bg-gray-700 rounded flex items-center justify-center">
                      <Building2 className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="font-medium">{language === "tr" ? "Havale / EFT" : "Bank Transfer"}</p>
                      <p className="text-sm text-muted-foreground">
                        {language === "tr" ? "Manuel onay gerektirir" : "Requires manual approval"}
                      </p>
                    </div>
                  </Label>
                </div>
              </RadioGroup>

              {/* Banka Hesapları (Havale seçiliyse) */}
              {paymentMethod === "bank_transfer" && (
                <div className="mt-6 space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    {language === "en" ? bankAccounts.instructions_en : bankAccounts.instructions}
                  </p>
                  
                  {bankAccounts.accounts
                    .filter(a => a.currency === selectedCurrency)
                    .map((account) => (
                      <div key={account.id} className="p-4 bg-white dark:bg-gray-900 rounded-lg border">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <p className="font-medium">{account.bank_name}</p>
                            <p className="text-sm text-muted-foreground">{account.account_holder}</p>
                          </div>
                          <Badge>{account.currency}</Badge>
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                          <code className="flex-1 text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded">
                            {account.iban}
                          </code>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => copyIban(account.iban, account.id)}
                            data-testid={`copy-iban-${account.id}`}
                          >
                            {copiedIban === account.id ? (
                              <Check className="h-4 w-4 text-green-500" />
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </div>
                    ))}
                  
                  <div className="mt-4">
                    <Label htmlFor="bankRef">
                      {language === "tr" ? "Transfer Referans No / Açıklama" : "Transfer Reference / Description"}
                    </Label>
                    <Input
                      id="bankRef"
                      value={bankReference}
                      onChange={(e) => setBankReference(e.target.value)}
                      placeholder={language === "tr" ? "Örn: EFT-12345 veya adınız" : "E.g.: EFT-12345 or your name"}
                      className="mt-1"
                      data-testid="bank-reference-input"
                    />
                  </div>
                </div>
              )}

              {/* Özet */}
              <div className="pt-4 border-t">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-muted-foreground">
                    {language === "tr" ? "Seçilen Paket:" : "Selected Package:"}
                  </span>
                  <span className="font-medium">
                    {language === "en" && selectedPackage.name_en ? selectedPackage.name_en : selectedPackage.name}
                  </span>
                </div>
                <div className="flex justify-between items-center mb-6">
                  <span className="text-muted-foreground">
                    {language === "tr" ? "Toplam:" : "Total:"}
                  </span>
                  <span className="text-2xl font-bold">{formatPrice(getPrice(selectedPackage))}</span>
                </div>

                <Button
                  className="w-full"
                  size="lg"
                  onClick={handleCheckout}
                  disabled={loading}
                  data-testid="checkout-button"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      {language === "tr" ? "İşleniyor..." : "Processing..."}
                    </>
                  ) : paymentMethod === "bank_transfer" ? (
                    <>
                      <Banknote className="h-4 w-4 mr-2" />
                      {language === "tr" ? "Havale Bildir" : "Submit Transfer"}
                    </>
                  ) : (
                    <>
                      <CreditCard className="h-4 w-4 mr-2" />
                      {language === "tr" ? "Ödemeye Geç" : "Proceed to Payment"}
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

// ==================== ÖDEME BAŞARILI ====================

export const PaymentSuccessPage = ({ token, t, language }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState("loading");
  const [transaction, setTransaction] = useState(null);

  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    const transactionId = searchParams.get("transaction_id");
    
    if (sessionId || transactionId) {
      pollPaymentStatus(sessionId || transactionId);
    }
  }, [searchParams]);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 5;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setStatus("timeout");
      return;
    }

    try {
      const response = await axios.get(`${API}/payments/status/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setTransaction(response.data);

      if (response.data.status === "completed") {
        setStatus("success");
      } else if (response.data.status === "failed" || response.data.status === "cancelled") {
        setStatus("failed");
      } else {
        setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
      }
    } catch (error) {
      console.error("Status check error:", error);
      setStatus("error");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
      <Card className="max-w-md w-full mx-4" data-testid="payment-result-card">
        <CardContent className="pt-6 text-center">
          {status === "loading" && (
            <>
              <Loader2 className="h-16 w-16 mx-auto mb-4 animate-spin text-blue-500" />
              <h2 className="text-xl font-bold mb-2">
                {language === "tr" ? "Ödeme kontrol ediliyor..." : "Checking payment..."}
              </h2>
            </>
          )}

          {status === "success" && (
            <>
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="h-10 w-10 text-green-500" />
              </div>
              <h2 className="text-xl font-bold mb-2 text-green-600">
                {language === "tr" ? "Ödeme Başarılı!" : "Payment Successful!"}
              </h2>
              <p className="text-muted-foreground mb-4">
                {language === "tr" 
                  ? `${transaction?.credits_added || 0} kredi hesabınıza eklendi.`
                  : `${transaction?.credits_added || 0} credits added to your account.`}
              </p>
              <Button onClick={() => navigate("/dashboard")} className="w-full" data-testid="go-dashboard">
                {language === "tr" ? "Panele Git" : "Go to Dashboard"}
              </Button>
            </>
          )}

          {(status === "failed" || status === "error") && (
            <>
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <XCircle className="h-10 w-10 text-red-500" />
              </div>
              <h2 className="text-xl font-bold mb-2 text-red-600">
                {language === "tr" ? "Ödeme Başarısız" : "Payment Failed"}
              </h2>
              <p className="text-muted-foreground mb-4">
                {transaction?.message || (language === "tr" ? "Bir hata oluştu." : "An error occurred.")}
              </p>
              <Button onClick={() => navigate("/payment")} variant="outline" className="w-full">
                {language === "tr" ? "Tekrar Dene" : "Try Again"}
              </Button>
            </>
          )}

          {status === "timeout" && (
            <>
              <div className="w-16 h-16 bg-yellow-100 dark:bg-yellow-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Loader2 className="h-10 w-10 text-yellow-500" />
              </div>
              <h2 className="text-xl font-bold mb-2">
                {language === "tr" ? "İşlem Bekliyor" : "Processing"}
              </h2>
              <p className="text-muted-foreground mb-4">
                {language === "tr" 
                  ? "Ödemeniz işleniyor. Lütfen birkaç dakika bekleyin."
                  : "Your payment is being processed. Please wait a few minutes."}
              </p>
              <Button onClick={() => navigate("/dashboard")} className="w-full">
                {language === "tr" ? "Panele Git" : "Go to Dashboard"}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== ÖDEME BEKLEMEDE ====================

export const PaymentPendingPage = ({ token, language }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const transactionId = searchParams.get("transaction_id");

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
      <Card className="max-w-md w-full mx-4" data-testid="payment-pending-card">
        <CardContent className="pt-6 text-center">
          <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
            <Building2 className="h-10 w-10 text-blue-500" />
          </div>
          <h2 className="text-xl font-bold mb-2">
            {language === "tr" ? "Havale Talebiniz Alındı" : "Transfer Request Received"}
          </h2>
          <p className="text-muted-foreground mb-4">
            {language === "tr" 
              ? "Havale/EFT işleminiz onaylandığında kredileriniz hesabınıza eklenecektir."
              : "Your credits will be added once the transfer is confirmed."}
          </p>
          {transactionId && (
            <p className="text-sm text-muted-foreground mb-4">
              {language === "tr" ? "İşlem No:" : "Transaction ID:"} <code>{transactionId.slice(0, 8)}...</code>
            </p>
          )}
          <Button onClick={() => navigate("/dashboard")} className="w-full" data-testid="go-dashboard-pending">
            {language === "tr" ? "Panele Git" : "Go to Dashboard"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== ÖDEME İPTAL ====================

export const PaymentCancelPage = ({ language }) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
      <Card className="max-w-md w-full mx-4" data-testid="payment-cancel-card">
        <CardContent className="pt-6 text-center">
          <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <XCircle className="h-10 w-10 text-gray-500" />
          </div>
          <h2 className="text-xl font-bold mb-2">
            {language === "tr" ? "Ödeme İptal Edildi" : "Payment Cancelled"}
          </h2>
          <p className="text-muted-foreground mb-4">
            {language === "tr" 
              ? "Ödeme işlemi iptal edildi. Dilediğiniz zaman tekrar deneyebilirsiniz."
              : "Payment was cancelled. You can try again anytime."}
          </p>
          <div className="space-y-2">
            <Button onClick={() => navigate("/payment")} className="w-full" data-testid="retry-payment">
              {language === "tr" ? "Tekrar Dene" : "Try Again"}
            </Button>
            <Button onClick={() => navigate("/dashboard")} variant="outline" className="w-full">
              {language === "tr" ? "Panele Git" : "Go to Dashboard"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PaymentPage;
