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
  Image,
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

// Maximum file size: 5MB
const MAX_FILE_SIZE = 5 * 1024 * 1024;

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
  const [uploadProgress, setUploadProgress] = useState('');
  
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
  
  const validateImageSize = (base64String: string): boolean => {
    // Approximate decoded size (base64 is ~33% larger than binary)
    const estimatedSize = (base64String.length * 3) / 4;
    return estimatedSize <= MAX_FILE_SIZE;
  };
  
  const uploadAvatarToBackend = async (base64Image: string): Promise<string> => {
    setUploadProgress('Uploading...');
    
    try {
      const response = await api.post('/profiles/avatar', {
        image_base64: base64Image
      });
      
      if (response.data.success) {
        setUploadProgress('');
        return response.data.avatar_url;
      } else {
        throw new Error(response.data.message || 'Upload failed');
      }
    } catch (error: any) {
      setUploadProgress('');
      const errorMessage = error.response?.data?.detail || error.message || 'Upload failed';
      throw new Error(errorMessage);
    }
  };
  
  const pickImage = async (useCamera: boolean) => {
    try {
      setUploadingPhoto(true);
      setUploadProgress('Preparing...');
      
      let result;
      if (useCamera) {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
          Alert.alert('Permission Required', 'Please allow camera access to take photos');
          setUploadingPhoto(false);
          setUploadProgress('');
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
          setUploadProgress('');
          return;
        }
        result = await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          allowsEditing: true,
          aspect: [1, 1],
          quality: 0.7,
          base64: true,
        });
      }
      
      if (!result.canceled && result.assets[0].base64) {
        const base64Data = result.assets[0].base64;
        
        // Validate file size
        if (!validateImageSize(base64Data)) {
          Alert.alert(
            'Image Too Large',
            'Please select an image smaller than 5MB for optimal performance.',
            [{ text: 'OK' }]
          );
          setUploadingPhoto(false);
          setUploadProgress('');
          return;
        }
        
        // Validate file type (expo-image-picker handles this, but double-check)
        const mimeType = result.assets[0].mimeType || '';
        if (!['image/jpeg', 'image/jpg', 'image/png'].includes(mimeType.toLowerCase())) {
          Alert.alert(
            'Invalid Format',
            'Only JPG and PNG images are allowed.',
            [{ text: 'OK' }]
          );
          setUploadingPhoto(false);
          setUploadProgress('');
          return;
        }
        
        // Upload to backend
        const imageWithPrefix = `data:image/jpeg;base64,${base64Data}`;
        const uploadedUrl = await uploadAvatarToBackend(imageWithPrefix);
        setProfilePhoto(uploadedUrl);
        
        Alert.alert('Success', 'Profile photo updated!');
      }
    } catch (error: any) {
      Alert.alert('Upload Failed', error.message || 'Failed to upload image');
    } finally {
      setUploadingPhoto(false);
      setUploadProgress('');
    }
  };
  
  const handlePhotoAction = () => {
    if (uploadingPhoto) return;
    
    Alert.alert(
      'Profile Photo',
      'Choose an option',
      [
        { text: 'Take Photo', onPress: () => pickImage(true) },
        { text: 'Choose from Library', onPress: () => pickImage(false) },
        profilePhoto ? { 
          text: 'Remove Photo', 
          onPress: async () => {
            setProfilePhoto('');
            // Update backend
            try {
              await updateProfile({ profile_photo: null });
            } catch {}
          }, 
          style: 'destructive' 
        } : null,
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
        // Profile photo is already saved via separate upload
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
  
  const isValidUrl = (urlString: string): boolean => {
    if (!urlString) return true;
    const pattern = /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/;
    return pattern.test(urlString);
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
          {/* Profile Photo Section */}
          <TouchableOpacity 
            style={styles.photoSection} 
            onPress={handlePhotoAction} 
            disabled={uploadingPhoto}
            activeOpacity={0.7}
          >
            <View style={styles.photoContainer}>
              {uploadingPhoto ? (
                <View style={styles.uploadingOverlay}>
                  <ActivityIndicator size="large" color={Colors.accent} />
                  {uploadProgress && (
                    <Text style={styles.uploadProgressText}>{uploadProgress}</Text>
                  )}
                </View>
              ) : profilePhoto && !profilePhoto.includes('base64') ? (
                <Image 
                  source={{ uri: profilePhoto }} 
                  style={styles.photoImage}
                />
              ) : profilePhoto ? (
                <Image 
                  source={{ uri: profilePhoto }} 
                  style={styles.photoImage}
                />
              ) : (
                <View style={styles.photoPlaceholder}>
                  <Ionicons name="camera" size={40} color={Colors.accent} />
                  <Text style={styles.photoText}>Add Photo</Text>
                </View>
              )}
              
              {/* Edit overlay badge */}
              {!uploadingPhoto && (
                <View style={styles.editBadge}>
                  <Ionicons name="pencil" size={14} color={Colors.background} />
                </View>
              )}
            </View>
            <Text style={styles.photoHint}>
              {uploadingPhoto ? 'Uploading...' : 'Tap to change photo'}
            </Text>
            <Text style={styles.photoSubhint}>JPG or PNG • Max 5MB</Text>
          </TouchableOpacity>
          
          {/* Form Fields */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Basic Info</Text>
            
            <Input
              label="Name *"
              value={fullName}
              onChangeText={setFullName}
              placeholder="Your name"
              autoCapitalize="words"
            />
            
            <Input
              label="Business Name"
              value={businessName}
              onChangeText={setBusinessName}
              placeholder="Your brand or business name"
              autoCapitalize="words"
            />
            
            <Input
              label="Salon Name"
              value={salonName}
              onChangeText={setSalonName}
              placeholder="Where you work"
              autoCapitalize="words"
            />
            
            <Input
              label="City"
              value={city}
              onChangeText={setCity}
              placeholder="Your city"
              autoCapitalize="words"
            />
          </View>
          
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>About You</Text>
            
            <Input
              label="Bio"
              value={bio}
              onChangeText={setBio}
              placeholder="Tell clients about yourself and your style..."
              multiline
              numberOfLines={4}
            />
            
            <Input
              label="Specialties"
              value={specialties}
              onChangeText={setSpecialties}
              placeholder="Hair color, balayage, cuts, extensions, etc."
            />
          </View>
          
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Social Links</Text>
            <Text style={styles.sectionSubtitle}>Connect with clients across platforms</Text>
            
            <Input
              label="Instagram"
              value={instagram}
              onChangeText={setInstagram}
              placeholder="@yourusername"
              autoCapitalize="none"
              autoCorrect={false}
              icon={<Ionicons name="logo-instagram" size={20} color={Colors.textSecondary} />}
            />
            
            <Input
              label="TikTok"
              value={tiktok}
              onChangeText={setTiktok}
              placeholder="@yourusername"
              autoCapitalize="none"
              autoCorrect={false}
              icon={<Ionicons name="logo-tiktok" size={20} color={Colors.textSecondary} />}
            />
            
            <Input
              label="Website"
              value={website}
              onChangeText={setWebsite}
              placeholder="https://yoursite.com"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
              icon={<Ionicons name="globe-outline" size={20} color={Colors.textSecondary} />}
            />
          </View>
          
          <Button
            title="Save Changes"
            onPress={handleSave}
            loading={loading}
            disabled={loading || uploadingPhoto}
            style={styles.saveButton}
          />
          
          <View style={styles.bottomPadding} />
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
    fontWeight: Typography.bold as any,
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
    position: 'relative',
  },
  photoImage: {
    width: '100%',
    height: '100%',
    borderWidth: 3,
    borderColor: Colors.accent,
    borderRadius: 60,
  },
  uploadingOverlay: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 3,
    borderColor: Colors.accent,
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  uploadProgressText: {
    fontSize: Typography.caption,
    color: Colors.accent,
    marginTop: Spacing.xs,
  },
  photoPlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 2,
    borderColor: Colors.border,
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  photoText: {
    fontSize: Typography.caption,
    color: Colors.text,
    marginTop: Spacing.xs,
  },
  editBadge: {
    position: 'absolute',
    bottom: 4,
    right: 4,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: Colors.background,
  },
  photoHint: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: Spacing.sm,
  },
  photoSubhint: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    marginTop: 2,
  },
  section: {
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  sectionSubtitle: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  saveButton: {
    marginTop: Spacing.md,
  },
  bottomPadding: {
    height: Spacing.xxl,
  },
});
