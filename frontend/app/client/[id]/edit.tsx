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
  ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import Input from '../../../components/Input';
import Button from '../../../components/Button';
import Colors from '../../../constants/Colors';
import Spacing from '../../../constants/Spacing';
import Typography from '../../../constants/Typography';
import api from '../../../utils/api';

export default function EditClientScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [notes, setNotes] = useState('');
  const [preferences, setPreferences] = useState('');
  const [hairGoals, setHairGoals] = useState('');
  const [isVip, setIsVip] = useState(false);
  const [photo, setPhoto] = useState('');
  const [rebookIntervalDays, setRebookIntervalDays] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<any>({});
  
  useEffect(() => {
    loadClient();
  }, [id]);
  
  const loadClient = async () => {
    try {
      const response = await api.get(`/clients/${id}`);
      const client = response.data;
      
      setName(client.name || '');
      setEmail(client.email || '');
      setPhone(client.phone || '');
      setNotes(client.notes || '');
      setPreferences(client.preferences || '');
      setHairGoals(client.hair_goals || '');
      setIsVip(client.is_vip || false);
      setPhoto(client.photo || '');
      setRebookIntervalDays(client.rebook_interval_days?.toString() || '');
    } catch (error) {
      Alert.alert('Error', 'Failed to load client data');
      router.back();
    } finally {
      setLoading(false);
    }
  };
  
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
    
    if (rebookIntervalDays && (isNaN(Number(rebookIntervalDays)) || Number(rebookIntervalDays) < 1)) {
      newErrors.rebookIntervalDays = 'Please enter a valid number of days';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSave = async () => {
    if (!validateForm()) return;
    
    setSaving(true);
    try {
      const response = await api.put(`/clients/${id}`, {
        name: name.trim(),
        email: email.trim() || null,
        phone: phone.trim() || null,
        photo: photo || null,
        notes: notes.trim() || null,
        preferences: preferences.trim() || null,
        hair_goals: hairGoals.trim() || null,
        is_vip: isVip,
        rebook_interval_days: rebookIntervalDays ? parseInt(rebookIntervalDays) : null,
      });
      
      Alert.alert('Success', 'Client updated successfully', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to update client');
    } finally {
      setSaving(false);
    }
  };
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.title}>Edit Client</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Loading client data...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
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
          <Text style={styles.title}>Edit Client</Text>
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
                  <Ionicons name="checkmark-circle" size={32} color={Colors.success} />
                  <Text style={styles.photoText}>Photo Added</Text>
                </View>
              ) : (
                <View style={styles.photoPlaceholder}>
                  <Ionicons name="camera" size={32} color={Colors.textSecondary} />
                  <Text style={styles.photoText}>Add Photo</Text>
                </View>
              )}
            </TouchableOpacity>
            {photo && (
              <TouchableOpacity 
                style={styles.removePhotoButton}
                onPress={() => setPhoto('')}
              >
                <Text style={styles.removePhotoText}>Remove Photo</Text>
              </TouchableOpacity>
            )}
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
          
          <Input
            label="Rebook Interval (Days)"
            value={rebookIntervalDays}
            onChangeText={setRebookIntervalDays}
            placeholder="e.g., 42 for 6 weeks"
            keyboardType="number-pad"
            error={errors.rebookIntervalDays}
          />
          <Text style={styles.helperText}>
            How often this client typically needs to rebook (for Smart Rebook alerts)
          </Text>
          
          {/* VIP Toggle */}
          <TouchableOpacity
            style={styles.vipToggle}
            onPress={() => setIsVip(!isVip)}
          >
            <View style={styles.vipLeft}>
              <Ionicons name="star" size={24} color={isVip ? Colors.vip : Colors.textSecondary} />
              <Text style={styles.vipText}>VIP Client</Text>
            </View>
            <View style={[styles.toggle, isVip && styles.toggleActive]}>
              <View style={[styles.toggleDot, isVip && styles.toggleDotActive]} />
            </View>
          </TouchableOpacity>
          
          <Button
            title="Save Changes"
            onPress={handleSave}
            loading={saving}
            style={styles.saveButton}
          />
        </ScrollView>
      </KeyboardAvoidingView>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: Spacing.md,
  },
  loadingText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
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
    backgroundColor: Colors.success + '20',
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
  removePhotoButton: {
    marginTop: Spacing.sm,
    padding: Spacing.sm,
  },
  removePhotoText: {
    fontSize: Typography.bodySmall,
    color: Colors.error,
  },
  helperText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: -Spacing.sm,
    marginBottom: Spacing.md,
    paddingHorizontal: 4,
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
});
