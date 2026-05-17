import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert, ActivityIndicator } from 'react-native'
import { useState, useEffect } from 'react'
import { useRouter } from 'expo-router'
import Purchases, { PurchasesPackage } from 'react-native-purchases'

const FEATURES = [
  '🤖 Unlimited AI coach messages',
  '🧠 Full 6-week CBT program',
  '⚡ AI craving predictor',
  '📊 Weekly personalized insights',
  '💬 Community posts + comments',
  '📓 Unlimited journal + export',
  '📈 Full analytics history',
]

export default function PaywallScreen() {
  const [packages, setPackages] = useState<PurchasesPackage[]>([])
  const [selectedPackage, setSelectedPackage] = useState<PurchasesPackage | null>(null)
  const [loading, setLoading] = useState(true)
  const [purchasing, setPurchasing] = useState(false)
  const router = useRouter()

  useEffect(() => {
    Purchases.getOfferings()
      .then((offerings) => {
        const pkgs = offerings.current?.availablePackages ?? []
        setPackages(pkgs)
        setSelectedPackage(pkgs.find((p) => p.packageType === 'MONTHLY') ?? pkgs[0] ?? null)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handlePurchase = async () => {
    if (!selectedPackage) return
    setPurchasing(true)
    try {
      await Purchases.purchasePackage(selectedPackage)
      Alert.alert('Welcome to Premium! 🎉', 'Your subscription is now active.')
      router.back()
    } catch (err: unknown) {
      const e = err as { userCancelled?: boolean; message?: string }
      if (!e.userCancelled) {
        Alert.alert('Purchase failed', e.message ?? 'Please try again.')
      }
    } finally {
      setPurchasing(false)
    }
  }

  const handleRestore = async () => {
    try {
      const info = await Purchases.restorePurchases()
      const isPremium = info.entitlements.active['premium'] !== undefined
      if (isPremium) {
        Alert.alert('Restored!', 'Your premium subscription has been restored.')
        router.back()
      } else {
        Alert.alert('No subscription found', 'No active subscription found for this account.')
      }
    } catch {
      Alert.alert('Restore failed', 'Please try again.')
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <TouchableOpacity style={styles.closeBtn} onPress={() => router.back()}>
        <Text style={styles.closeBtnText}>✕</Text>
      </TouchableOpacity>

      <Text style={styles.headline}>Go Premium</Text>
      <Text style={styles.subheadline}>Everything you need to quit for good</Text>

      <View style={styles.featureList}>
        {FEATURES.map((f) => (
          <View key={f} style={styles.featureRow}>
            <Text style={styles.featureText}>{f}</Text>
          </View>
        ))}
      </View>

      {loading ? (
        <ActivityIndicator color="#16a34a" style={{ marginVertical: 24 }} />
      ) : (
        <View style={styles.packageRow}>
          {packages.map((pkg) => (
            <TouchableOpacity
              key={pkg.identifier}
              style={[styles.packageBtn, selectedPackage?.identifier === pkg.identifier && styles.packageBtnSelected]}
              onPress={() => setSelectedPackage(pkg)}
            >
              <Text style={[styles.packageTitle, selectedPackage?.identifier === pkg.identifier && styles.packageTitleSelected]}>
                {pkg.product.title}
              </Text>
              <Text style={[styles.packagePrice, selectedPackage?.identifier === pkg.identifier && styles.packagePriceSelected]}>
                {pkg.product.priceString}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <TouchableOpacity
        style={[styles.purchaseBtn, purchasing && styles.purchaseBtnDisabled]}
        onPress={handlePurchase}
        disabled={purchasing || !selectedPackage}
      >
        <Text style={styles.purchaseBtnText}>
          {purchasing ? 'Processing...' : `Start Premium — ${selectedPackage?.product.priceString ?? ''}/mo`}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={handleRestore} style={styles.restoreBtn}>
        <Text style={styles.restoreBtnText}>Restore Purchase</Text>
      </TouchableOpacity>

      <Text style={styles.disclaimer}>
        Cancel anytime. Billed monthly via App Store / Google Play.
      </Text>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0fdf4' },
  content: { padding: 24, paddingTop: 60, paddingBottom: 48 },
  closeBtn: { position: 'absolute', top: 16, right: 20, zIndex: 10 },
  closeBtnText: { fontSize: 22, color: '#6b7280' },
  headline: { fontSize: 32, fontWeight: 'bold', color: '#111827', textAlign: 'center', marginBottom: 8 },
  subheadline: { fontSize: 16, color: '#6b7280', textAlign: 'center', marginBottom: 32 },
  featureList: { gap: 12, marginBottom: 32 },
  featureRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  featureText: { fontSize: 15, color: '#111827', fontWeight: '500' },
  packageRow: { flexDirection: 'row', gap: 12, marginBottom: 24 },
  packageBtn: { flex: 1, borderWidth: 2, borderColor: '#e5e7eb', borderRadius: 12, padding: 16, alignItems: 'center', backgroundColor: 'white' },
  packageBtnSelected: { borderColor: '#16a34a', backgroundColor: '#f0fdf4' },
  packageTitle: { fontSize: 14, fontWeight: '600', color: '#6b7280', marginBottom: 4 },
  packageTitleSelected: { color: '#15803d' },
  packagePrice: { fontSize: 20, fontWeight: 'bold', color: '#111827' },
  packagePriceSelected: { color: '#16a34a' },
  purchaseBtn: { backgroundColor: '#16a34a', borderRadius: 14, padding: 18, alignItems: 'center', marginBottom: 12 },
  purchaseBtnDisabled: { opacity: 0.6 },
  purchaseBtnText: { color: 'white', fontSize: 16, fontWeight: '700' },
  restoreBtn: { alignItems: 'center', padding: 12 },
  restoreBtnText: { color: '#6b7280', fontSize: 14 },
  disclaimer: { textAlign: 'center', fontSize: 12, color: '#9ca3af', marginTop: 16 },
})
