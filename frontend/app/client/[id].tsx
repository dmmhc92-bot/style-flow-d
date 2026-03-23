import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import LoadingSpinner from '../../components/LoadingSpinner';

export default function ClientDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  
  const [client, setClient] = useState<any>(null);
  const [formulas, setFormulas] = useState([]);
  const [gallery, setGallery] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const loadClientData = useCallback(async () => {
    try {
      const [clientRes, formulasRes, galleryRes] = await Promise.all([
        api.get(`/clients/${id}`),
        api.get(`/formulas?client_id=${id}`),
        api.get(`/gallery?client_id=${id}`),
      ]);
      
      setClient(clientRes.data);
      setFormulas(formulasRes.data);
      setGallery(galleryRes.data);
    } catch (error) {
      console.error('Failed to load client data:', error);
      Alert.alert('Error', 'Failed to load client details');
      router.back();
    } finally {
      setLoading(false);
    }
  }, [id]);
  
  // Refresh data when screen comes into focus (handles navigation back)
  useFocusEffect(
    useCallback(() => {
      loadClientData();
    }, [loadClientData])
  );
  
  const handleDelete = () => {
    Alert.alert(
      'Delete Client',
      'Are you sure you want to delete this client? This will also delete all associated data.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/clients/${id}`);
              Alert.alert('Success', 'Client deleted', [
                { text: 'OK', onPress: () => router.back() },
              ]);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete client');
            }
          },
        },
      ]
    );
  };
  
  if (loading || !client) {
    return <LoadingSpinner />;
  }
  
  const InfoRow = ({ icon, label, value }: any) => {
    if (!value) return null;
    
    return (
      <View style={styles.infoRow}>
        <Ionicons name={icon} size={20} color={Colors.textSecondary} />
        <View style={styles.infoContent}>
          <Text style={styles.infoLabel}>{label}</Text>
          <Text style={styles.infoValue}>{value}</Text>
        </View>
      </View>
    );
  };
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Client Details</Text>
        <TouchableOpacity
          style={styles.editButton}
          onPress={() => Alert.alert('Coming Soon', 'Edit client feature')}
        >
          <Ionicons name="create-outline" size={24} color={Colors.accent} />
        </TouchableOpacity>
      </View>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Client Info */}
        <Card style={styles.profileCard}>
          <View style={styles.profileHeader}>
            <View style={styles.avatar}>
              <Ionicons name="person" size={40} color={Colors.textSecondary} />
            </View>
            <View style={styles.profileInfo}>
              <View style={styles.nameRow}>
                <Text style={styles.name}>{client.name}</Text>
                {client.is_vip && (
                  <Ionicons name="star" size={20} color={Colors.vip} />
                )}
              </View>
              <Text style={styles.visitCount}>
                {client.visit_count} visit{client.visit_count !== 1 ? 's' : ''}
              </Text>
            </View>
          </View>
          
          <View style={styles.divider} />
          
          <InfoRow icon="mail-outline" label="Email" value={client.email} />
          <InfoRow icon="call-outline" label="Phone" value={client.phone} />
          <InfoRow icon="cut-outline" label="Hair Goals" value={client.hair_goals} />
          <InfoRow icon="heart-outline" label="Preferences" value={client.preferences} />
          <InfoRow icon="document-text-outline" label="Notes" value={client.notes} />
        </Card>
        
        {/* Quick Actions */}
        <View style={styles.actionsGrid}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push(`/appointment/add?clientId=${id}`)}
          >
            <Ionicons name="calendar" size={24} color={Colors.accent} />
            <Text style={styles.actionText}>Book</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push(`/client/${id}/formula`)}
          >
            <Ionicons name="flask" size={24} color={Colors.accent} />
            <Text style={styles.actionText}>Formula</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push(`/client/${id}/photos`)}
          >
            <Ionicons name="camera" size={24} color={Colors.accent} />
            <Text style={styles.actionText}>Photos</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push(`/client/${id}/visits`)}
          >
            <Ionicons name="time" size={24} color={Colors.accent} />
            <Text style={styles.actionText}>Visits</Text>
          </TouchableOpacity>
        </View>
        
        {/* Formulas */}
        {formulas.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Formulas ({formulas.length})</Text>
            {formulas.map((formula: any) => (
              <Card key={formula.id} style={styles.formulaCard}>
                <Text style={styles.formulaName}>{formula.formula_name}</Text>
                <Text style={styles.formulaDetails}>{formula.formula_details}</Text>
              </Card>
            ))}
          </View>
        )}
        
        {/* Gallery */}
        {gallery.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Gallery ({gallery.length})</Text>
            <Text style={styles.galleryNote}>Before & after photos available</Text>
          </View>
        )}
        
        {/* Delete Button */}
        <Button
          title="Delete Client"
          onPress={handleDelete}
          variant="outline"
          style={styles.deleteButton}
          textStyle={{ color: Colors.error }}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  editButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    padding: Spacing.screenPadding,
  },
  profileCard: {
    marginBottom: Spacing.lg,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  profileInfo: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  name: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginRight: Spacing.sm,
  },
  visitCount: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.border,
    marginVertical: Spacing.md,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: Spacing.md,
  },
  infoContent: {
    flex: 1,
    marginLeft: Spacing.md,
  },
  infoLabel: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginBottom: 2,
  },
  infoValue: {
    fontSize: Typography.body,
    color: Colors.text,
  },
  actionsGrid: {
    flexDirection: 'row',
    marginHorizontal: -Spacing.xs,
    marginBottom: Spacing.lg,
  },
  actionButton: {
    flex: 1,
    marginHorizontal: Spacing.xs,
    backgroundColor: Colors.cardBackground,
    borderRadius: 12,
    padding: Spacing.md,
    alignItems: 'center',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  actionText: {
    fontSize: Typography.caption,
    color: Colors.text,
    marginTop: Spacing.xs,
    fontWeight: Typography.medium,
  },
  section: {
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  formulaCard: {
    marginBottom: Spacing.sm,
  },
  formulaName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  formulaDetails: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  galleryNote: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  deleteButton: {
    marginTop: Spacing.md,
    borderColor: Colors.error,
  },
});