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
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import { useAuthStore } from '../../store/authStore';
import api from '../../utils/api';

export default function ProfileEditScreen() {
  const router = useRouter();
  const { user, updateProfile, loadUser } = useAuthStore();
  
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [businessName, setBusinessName] = useState(user?.business_name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [city, setCity] = useState(user?.city || '');
  const [salonName, setSalonName] = useState(user?.salon_name || '');
  const [specialties, setSpecialties] = useState(user?.specialties || '');
  const [instagram, setInstagram] = useState(user?.instagram_handle || '');
  const [tiktok, setTiktok] = useState(user?.tiktok_handle || '');
  const [website, setWebsite] = useState(user?.website_url || '');
  const [profilePhoto, setProfilePhoto] = useState(user?.profile_photo || '');
  const [loading, setLoading] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  
  // Load user data on mount and populate form when user changes
  useEffect(() => {
    loadUser();
  }, []);
  
  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setBusinessName(user.business_name || '');
      setBio(user.bio || '');
      setCity(user.city || '');
      setSalonName(user.salon_name || '');
      setSpecialties(user.specialties || '');
      setInstagram(user.instagram_handle || '');
      setTiktok(user.tiktok_handle || '');
      setWebsite(user.website_url || '');
      setProfilePhoto(user.profile_photo || '');
    }
  }, [user]);
  
  const pickImage = async (useCamera: boolean) => {
    try {
      setUploadingPhoto(true);
      
      let result;
      if (useCamera) {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
          Alert.alert('Permission Required', 'Please allow camera access');
          setUploadingPhoto(false);
          return;
        }
        result = await ImagePicker.launchCameraAsync({
          allowsEditing: true,
          aspect: [1, 1],
          quality: 0.7,
          base64: true,
        });
      } else {
        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
          Alert.alert('Permission Required', 'Please allow photo library access');
          setUploadingPhoto(false);
          return;
        }
        result = await ImagePicker.launchImagePickerAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          allowsEditing: true,
          aspect: [1, 1],
          quality: 0.7,
          base64: true,
        });
      }
      
      if (!result.canceled && result.assets[0].base64) {
        setProfilePhoto(`data:image/jpeg;base64,${result.assets[0].base64}`);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to select image');
    } finally {
      setUploadingPhoto(false);
    }
  };
  
  const handlePhotoAction = () => {
    Alert.alert(
      'Profile Photo',
      'Choose an option',
      [
        { text: 'Take Photo', onPress: () => pickImage(true) },
        { text: 'Choose from Library', onPress: () => pickImage(false) },
        profilePhoto ? { text: 'Remove Photo', onPress: () => setProfilePhoto(''), style: 'destructive' } : null,
        { text: 'Cancel', style: 'cancel' },
      ].filter(Boolean) as any
    );
  };
  
  const handleSave = async () => {
    if (!fullName.trim()) {
      Alert.alert('Error', 'Name is required');
      return;
    }
    
    setLoading(true);
    try {
      await updateProfile({
        full_name: fullName.trim(),
        business_name: businessName.trim() || undefined,
        bio: bio.trim() || undefined,
        city: city.trim() || undefined,
        salon_name: salonName.trim() || undefined,
        specialties: specialties.trim() || undefined,
        instagram_handle: instagram.trim() || undefined,
        tiktok_handle: tiktok.trim() || undefined,
        website_url: website.trim() || undefined,
        profile_photo: profilePhoto || undefined,
      });
      
      Alert.alert('Success', 'Profile updated successfully', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to update profile');
    } finally {
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
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.title}>Edit Profile</Text>
          <View style={{ width: 40 }} />
        </View>
        
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <TouchableOpacity style={styles.photoSection} onPress={handlePhotoAction} disabled={uploadingPhoto}>
            <View style={styles.photoContainer}>
              {uploadingPhoto ? (
                <ActivityIndicator size="large" color={Colors.accent} />
              ) : profilePhoto ? (
                <View style={styles.photoPreview}>
                  <Text style={styles.photoText}>Photo Set</Text>
                </View>
              ) : (
                <View style={styles.photoPlaceholder}>
                  <Ionicons name="camera" size={40} color={Colors.accent} />
                  <Text style={styles.photoText}>Add Photo</Text>
                </View>
              )}
            </View>
            <Text style={styles.photoHint}>Tap to change photo</Text>
          </TouchableOpacity>
          
          <Input
            label="Name *"
            value={fullName}
            onChangeText={setFullName}
            placeholder="Your name"
          />
          
          <Input
            label="Business Name"
            value={businessName}
            onChangeText={setBusinessName}
            placeholder="Salon or business name"
          />
          
          <Input
            label="Salon Name"
            value={salonName}
            onChangeText={setSalonName}
            placeholder="Where you work"
          />
          
          <Input
            label="City"
            value={city}
            onChangeText={setCity}
            placeholder="Your city"
          />
          
          <Input
            label="Bio"
            value={bio}
            onChangeText={setBio}
            placeholder="Tell others about yourself"
            multiline
            numberOfLines={4}
          />
          
          <Input
            label="Specialties"
            value={specialties}
            onChangeText={setSpecialties}
            placeholder="Hair color, cuts, extensions, etc."
          />
          
          <Input
            label="Instagram"
            value={instagram}
            onChangeText={setInstagram}
            placeholder="@username"
            autoCapitalize="none"
          />
          
          <Input
            label="TikTok"
            value={tiktok}
            onChangeText={setTiktok}
            placeholder="@username"
            autoCapitalize="none"
          />
          
          <Input
            label="Website"
            value={website}
            onChangeText={setWebsite}
            placeholder="https://yoursite.com"
            autoCapitalize="none"
            keyboardType="url"
          />
          
          <Button
            title="Save Changes"
            onPress={handleSave}
            loading={loading}
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
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
  },
  photoSection: {
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  photoContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    overflow: 'hidden',
  },
  photoPreview: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.accent + '30',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: Colors.accent,
  },
  photoPlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.backgroundCard,
    borderWidth: 2,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  photoText: {
    fontSize: Typography.caption,
    color: Colors.text,
    marginTop: Spacing.xs,
  },
  photoHint: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: Spacing.sm,
  },
  saveButton: {
    marginTop: Spacing.lg,
    marginBottom: Spacing.xl,
  },
});