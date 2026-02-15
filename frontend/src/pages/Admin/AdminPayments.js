import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
  CreditCard, CheckCircle, XCircle, Loader2, Clock, DollarSign,
  Building2, RefreshCw, Eye, Check, X, TrendingUp, Users
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AdminPayments = ({ token, language }) => {
  const [transactions, setTransactions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [methodFilter, setMethodFilter] = useState("all");
  
  // Dialog states
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, [filter, methodFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      let url = `${API}/payments/admin/transactions`;
      const params = new URLSearchParams();
      if (filter !== "all") params.append("status", filter);
      if (methodFilter !== "all") params.append("payment_method", methodFilter);
      if (params.toString()) url += `?${params.toString()}`;
      
      const [transRes, analyticsRes] = await Promise.all([
        axios.get(url, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/payments/admin/analytics`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setTransactions(transRes.data);
      setAnalytics(analyticsRes.data);
    } catch (error) {
      console.error("Data fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  const approveTransaction = async (transactionId) => {
    try {
      setActionLoading(true);
      await axios.patch(
        `${API}/payments/admin/transactions/${transactionId}/approve`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchData();
    } catch (error) {
      console.error("Approve error:", error);
      alert(error.response?.data?.detail || "Onaylama hatası");
    } finally {
      setActionLoading(false);
    }
  };

  const rejectTransaction = async () => {
    if (!selectedTransaction || !rejectReason.trim()) return;
    
    try {
      setActionLoading(true);
      await axios.patch(
        `${API}/payments/admin/transactions/${selectedTransaction.id}/reject`,
        { reason: rejectReason },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setShowRejectDialog(false);
      setRejectReason("");
      setSelectedTransaction(null);
      fetchData();
    } catch (error) {
      console.error("Reject error:", error);
      alert(error.response?.data?.detail || "Reddetme hatası");
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString(language === "tr" ? "tr-TR" : "en-US");
  };

  const formatCurrency = (amount, currency) => {
    const symbols = { TRY: "₺", USD: "$", EUR: "€" };
    return `${symbols[currency] || ""}${amount.toFixed(2)}`;
  };

  const getStatusBadge = (status) => {
    const config = {
      pending: { variant: "outline", color: "text-yellow-600", icon: Clock },
      completed: { variant: "default", color: "text-green-600 bg-green-100", icon: CheckCircle },
      failed: { variant: "destructive", color: "text-red-600", icon: XCircle },
      cancelled: { variant: "secondary", color: "text-gray-600", icon: X }
    };
    const { variant, color, icon: Icon } = config[status] || config.pending;
    return (
      <Badge variant={variant} className={color}>
        <Icon className="h-3 w-3 mr-1" />
        {status.toUpperCase()}
      </Badge>
    );
  };

  const getMethodBadge = (method) => {
    const config = {
      stripe: { color: "bg-purple-100 text-purple-700", label: "Stripe" },
      iyzico: { color: "bg-blue-100 text-blue-700", label: "iyzico" },
      bank_transfer: { color: "bg-gray-100 text-gray-700", label: "Havale/EFT" }
    };
    const { color, label } = config[method] || { color: "bg-gray-100", label: method };
    return <Badge className={color}>{label}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {language === "tr" ? "Toplam İşlem" : "Total Transactions"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.total_transactions}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {language === "tr" ? "Tamamlanan" : "Completed"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{analytics.by_status.completed}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {language === "tr" ? "Bekleyen" : "Pending"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{analytics.by_status.pending}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {language === "tr" ? "Toplam Gelir" : "Total Revenue"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {Object.entries(analytics.revenue_by_currency || {}).map(([currency, amount]) => (
                  <div key={currency} className="text-lg font-bold">
                    {formatCurrency(amount, currency)}
                  </div>
                ))}
                {Object.keys(analytics.revenue_by_currency || {}).length === 0 && (
                  <div className="text-lg font-bold text-muted-foreground">-</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              {language === "tr" ? "Ödeme İşlemleri" : "Payment Transactions"}
            </CardTitle>
            <div className="flex gap-2">
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm"
                data-testid="status-filter"
              >
                <option value="all">{language === "tr" ? "Tüm Durumlar" : "All Status"}</option>
                <option value="pending">{language === "tr" ? "Bekleyen" : "Pending"}</option>
                <option value="completed">{language === "tr" ? "Tamamlanan" : "Completed"}</option>
                <option value="failed">{language === "tr" ? "Başarısız" : "Failed"}</option>
              </select>
              <select
                value={methodFilter}
                onChange={(e) => setMethodFilter(e.target.value)}
                className="px-3 py-2 border rounded-md text-sm"
                data-testid="method-filter"
              >
                <option value="all">{language === "tr" ? "Tüm Yöntemler" : "All Methods"}</option>
                <option value="stripe">Stripe</option>
                <option value="iyzico">iyzico</option>
                <option value="bank_transfer">{language === "tr" ? "Havale/EFT" : "Bank Transfer"}</option>
              </select>
              <Button variant="outline" size="icon" onClick={fetchData} data-testid="refresh-button">
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : transactions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {language === "tr" ? "İşlem bulunamadı" : "No transactions found"}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2">{language === "tr" ? "Tarih" : "Date"}</th>
                    <th className="text-left py-3 px-2">{language === "tr" ? "Kullanıcı" : "User"}</th>
                    <th className="text-left py-3 px-2">{language === "tr" ? "Paket" : "Package"}</th>
                    <th className="text-left py-3 px-2">{language === "tr" ? "Tutar" : "Amount"}</th>
                    <th className="text-left py-3 px-2">{language === "tr" ? "Yöntem" : "Method"}</th>
                    <th className="text-left py-3 px-2">{language === "tr" ? "Durum" : "Status"}</th>
                    <th className="text-left py-3 px-2">{language === "tr" ? "İşlem" : "Action"}</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => (
                    <tr key={tx.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="py-3 px-2 text-sm">{formatDate(tx.created_at)}</td>
                      <td className="py-3 px-2">
                        <div className="text-sm font-medium">{tx.user_email}</div>
                      </td>
                      <td className="py-3 px-2">
                        <div className="text-sm">{tx.package_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {tx.credits_to_add} {language === "tr" ? "kredi" : "credits"}
                        </div>
                      </td>
                      <td className="py-3 px-2 font-medium">
                        {formatCurrency(tx.amount, tx.currency)}
                      </td>
                      <td className="py-3 px-2">{getMethodBadge(tx.payment_method)}</td>
                      <td className="py-3 px-2">{getStatusBadge(tx.status)}</td>
                      <td className="py-3 px-2">
                        {tx.payment_method === "bank_transfer" && tx.status === "pending" && (
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-green-600 hover:bg-green-50"
                              onClick={() => approveTransaction(tx.id)}
                              disabled={actionLoading}
                              data-testid={`approve-${tx.id}`}
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600 hover:bg-red-50"
                              onClick={() => {
                                setSelectedTransaction(tx);
                                setShowRejectDialog(true);
                              }}
                              disabled={actionLoading}
                              data-testid={`reject-${tx.id}`}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                        {tx.bank_reference && (
                          <div className="text-xs text-muted-foreground mt-1">
                            Ref: {tx.bank_reference}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reject Dialog */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{language === "tr" ? "Ödemeyi Reddet" : "Reject Payment"}</DialogTitle>
            <DialogDescription>
              {language === "tr" 
                ? "Bu ödemeyi reddetmek için bir sebep girin."
                : "Enter a reason for rejecting this payment."}
            </DialogDescription>
          </DialogHeader>
          <Textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder={language === "tr" ? "Reddetme sebebi..." : "Rejection reason..."}
            className="min-h-[100px]"
            data-testid="reject-reason"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectDialog(false)}>
              {language === "tr" ? "İptal" : "Cancel"}
            </Button>
            <Button
              variant="destructive"
              onClick={rejectTransaction}
              disabled={!rejectReason.trim() || actionLoading}
              data-testid="confirm-reject"
            >
              {actionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : (language === "tr" ? "Reddet" : "Reject")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminPayments;
