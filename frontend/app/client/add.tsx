import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { useTrialAction, TrialBadge } from '../../components/PremiumGate';
import { useTrialStore } from '../../store/trialStore';

export default function AddClientScreen() {
  const router = useRouter();
  
  // Trial system integration
  const { canPerformAction, performAction, remainingUses, isPremium, PaywallModal } = useTrialAction('clientsCreated');
  const { loadUsage } = useTrialStore();
  
  // Load trial usage on mount
  useEffect(() => {
    loadUsage();
  }, []);
  
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [notes, setNotes] = useState('');
  const [preferences, setPreferences] = useState('');
  const [hairGoals, setHairGoals] = useState('');
  const [isVip, setIsVip] = useState(false);
  const [photo, setPhoto] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});
  
  const pickImage = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (permissionResult.granted === false) {
      Alert.alert('Permission Required', 'Please allow access to your photo library');
      return;
    }
    
    const result = await ImagePicker.launchImagePickerAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.7,
      base64: true,
    });
    
    if (!result.canceled && result.assets[0].base64) {
      setPhoto(`data:image/jpeg;base64,${result.assets[0].base64}`);
    }
  };
  
  const validateForm = () => {
    const newErrors: any = {};
    
    if (!name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (email && !/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email is invalid';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSave = async () => {
    if (!validateForm()) return;
    
    // Check trial/subscription status before creating
    if (!canPerformAction) {
      // Paywall will be shown automatically
      return;
    }
    
    setLoading(true);
    try {
      // Track this as a premium action (increment trial usage)
      await performAction();
      
      const response = await api.post('/clients', {
        name: name.trim(),
        email: email.trim() || null,
        phone: phone.trim() || null,
        photo: photo || null,
        notes: notes.trim() || null,
        preferences: preferences.trim() || null,
        hair_goals: hairGoals.trim() || null,
        is_vip: isVip,
      });
      
      // Navigate to clients list after successful save
      router.replace('/tabs/clients');
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to add client');
      setLoading(false);
    }
  };
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.title}>Add Client</Text>
          <View style={{ width: 40 }} />
        </View>
        
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* Photo */}
          <View style={styles.photoSection}>
            <TouchableOpacity
              style={styles.photoButton}
              onPress={pickImage}
            >
              {photo ? (
                <View style={styles.photoPreview}>
                  <Text>Photo Added</Text>
                </View>
              ) : (
                <View style={styles.photoPlaceholder}>
                  <Ionicons name="camera" size={32} color={Colors.textSecondary} />
                  <Text style={styles.photoText}>Add Photo</Text>
                </View>
              )}
            </TouchableOpacity>
          </View>
          
          <Input
            label="Name *"
            value={name}
            onChangeText={setName}
            placeholder="Client name"
            error={errors.name}
          />
          
          <Input
            label="Email"
            value={email}
            onChangeText={setEmail}
            placeholder="email@example.com"
            keyboardType="email-address"
            autoCapitalize="none"
            error={errors.email}
          />
          
          <Input
            label="Phone"
            value={phone}
            onChangeText={setPhone}
            placeholder="(555) 123-4567"
            keyboardType="phone-pad"
          />
          
          <Input
            label="Hair Goals"
            value={hairGoals}
            onChangeText={setHairGoals}
            placeholder="What are they looking to achieve?"
            multiline
            numberOfLines={3}
          />
          
          <Input
            label="Preferences"
            value={preferences}
            onChangeText={setPreferences}
            placeholder="Color preferences, styles, etc."
            multiline
            numberOfLines={3}
          />
          
          <Input
            label="Notes"
            value={notes}
            onChangeText={setNotes}
            placeholder="Any additional notes"
            multiline
            numberOfLines={4}
          />
          
          {/* VIP Toggle */}
          <TouchableOpacity
            style={styles.vipToggle}
            onPress={() => setIsVip(!isVip)}
          >
            <View style={styles.vipLeft}>
              <Ionicons name="star" size={24} color={isVip ? Colors.vip : Colors.textSecondary} />
              <Text style={styles.vipText}>Mark as VIP Client</Text>
            </View>
            <View style={[styles.toggle, isVip && styles.toggleActive]}>
              <View style={[styles.toggleDot, isVip && styles.toggleDotActive]} />
            </View>
          </TouchableOpacity>
          
          <Button
            title="Save Client"
            onPress={handleSave}
            loading={loading}
            style={styles.saveButton}
          />
          
          {/* Show remaining trial uses */}
          {!isPremium && remainingUses > 0 && (
            <View style={styles.trialInfo}>
              <TrialBadge />
              <Text style={styles.trialText}>{remainingUses} free client{remainingUses !== 1 ? 's' : ''} remaining</Text>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
      
      {/* Paywall Modal */}
      <PaywallModal />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  keyboardView: {
    flex: 1,
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
  scrollContent: {
    padding: Spacing.screenPadding,
  },
  photoSection: {
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  photoButton: {
    width: 120,
    height: 120,
    borderRadius: 60,
    overflow: 'hidden',
  },
  photoPreview: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  photoPlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  photoText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
  vipToggle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    padding: Spacing.md,
    borderRadius: 12,
    marginBottom: Spacing.lg,
  },
  vipLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  vipText: {
    fontSize: Typography.body,
    color: Colors.text,
    marginLeft: Spacing.md,
    fontWeight: Typography.medium,
  },
  toggle: {
    width: 50,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.border,
    padding: 2,
    justifyContent: 'center',
  },
  toggleActive: {
    backgroundColor: Colors.vip,
  },
  toggleDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: Colors.background,
  },
  toggleDotActive: {
    alignSelf: 'flex-end',
  },
  saveButton: {
    marginTop: Spacing.md,
  },
  trialInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: Spacing.md,
    padding: Spacing.sm,
    backgroundColor: Colors.accent + '10',
    borderRadius: Spacing.radiusMedium,
    gap: Spacing.xs,
  },
  trialText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
});