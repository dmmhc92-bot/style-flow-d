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
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Calendar } from 'react-native-calendars';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { format } from 'date-fns';

export default function AddAppointmentScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [service, setService] = useState('');
  const [duration, setDuration] = useState('60');
  const [notes, setNotes] = useState('');
  const [showCalendar, setShowCalendar] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});
  
  useEffect(() => {
    loadClients();
  }, []);
  
  const loadClients = async () => {
    try {
      const response = await api.get('/clients');
      setClients(response.data);
      
      if (params.clientId) {
        setSelectedClient(params.clientId as string);
      }
    } catch (error) {
      console.error('Failed to load clients:', error);
    }
  };
  
  const validateForm = () => {
    const newErrors: any = {};
    
    if (!selectedClient) {
      newErrors.client = 'Please select a client';
    }
    
    if (!selectedDate) {
      newErrors.date = 'Please select a date';
    }
    
    if (!selectedTime) {
      newErrors.time = 'Please select a time';
    }
    
    if (!service.trim()) {
      newErrors.service = 'Service is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSave = async () => {
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      const appointmentDateTime = new Date(`${selectedDate}T${selectedTime}:00`);
      
      await api.post('/appointments', {
        client_id: selectedClient,
        appointment_date: appointmentDateTime.toISOString(),
        service: service.trim(),
        duration_minutes: parseInt(duration),
        notes: notes.trim() || null,
        status: 'scheduled',
      });
      
      Alert.alert('Success', 'Appointment scheduled successfully', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to schedule appointment');
    } finally {
      setLoading(false);
    }
  };
  
  const timeSlots = [
    '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
    '15:00', '15:30', '16:00', '16:30', '17:00', '17:30',
  ];
  
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
          <Text style={styles.title}>New Appointment</Text>
          <View style={{ width: 40 }} />
        </View>
        
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* Client Selection */}
          <View style={styles.section}>
            <Text style={styles.label}>Client *</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.clientScroll}
            >
              {clients.map((client: any) => (
                <TouchableOpacity
                  key={client.id}
                  style={[
                    styles.clientChip,
                    selectedClient === client.id && styles.clientChipActive,
                  ]}
                  onPress={() => setSelectedClient(client.id)}
                >
                  <Text
                    style={[
                      styles.clientChipText,
                      selectedClient === client.id && styles.clientChipTextActive,
                    ]}
                  >
                    {client.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
            {errors.client && <Text style={styles.error}>{errors.client}</Text>}
          </View>
          
          {/* Calendar */}
          <View style={styles.section}>
            <Text style={styles.label}>Date *</Text>
            <Calendar
              minDate={new Date().toISOString().split('T')[0]}
              onDayPress={(day: any) => {
                setSelectedDate(day.dateString);
                setShowCalendar(false);
              }}
              markedDates={{
                [selectedDate]: {
                  selected: true,
                  selectedColor: Colors.accent,
                },
              }}
              theme={{
                todayTextColor: Colors.accent,
                selectedDayBackgroundColor: Colors.accent,
                selectedDayTextColor: Colors.textInverse,
                arrowColor: Colors.accent,
              }}
            />
            {errors.date && <Text style={styles.error}>{errors.date}</Text>}
          </View>
          
          {/* Time Selection */}
          {selectedDate && (
            <View style={styles.section}>
              <Text style={styles.label}>Time *</Text>
              <View style={styles.timeGrid}>
                {timeSlots.map((time) => (
                  <TouchableOpacity
                    key={time}
                    style={[
                      styles.timeSlot,
                      selectedTime === time && styles.timeSlotActive,
                    ]}
                    onPress={() => setSelectedTime(time)}
                  >
                    <Text
                      style={[
                        styles.timeText,
                        selectedTime === time && styles.timeTextActive,
                      ]}
                    >
                      {time}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
              {errors.time && <Text style={styles.error}>{errors.time}</Text>}
            </View>
          )}
          
          <Input
            label="Service *"
            value={service}
            onChangeText={setService}
            placeholder="Haircut, Color, etc."
            error={errors.service}
          />
          
          <View style={styles.section}>
            <Text style={styles.label}>Duration (minutes)</Text>
            <View style={styles.durationButtons}>
              {['30', '60', '90', '120'].map((d) => (
                <TouchableOpacity
                  key={d}
                  style={[
                    styles.durationButton,
                    duration === d && styles.durationButtonActive,
                  ]}
                  onPress={() => setDuration(d)}
                >
                  <Text
                    style={[
                      styles.durationText,
                      duration === d && styles.durationTextActive,
                    ]}
                  >
                    {d}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
          
          <Input
            label="Notes"
            value={notes}
            onChangeText={setNotes}
            placeholder="Any additional notes"
            multiline
            numberOfLines={3}
          />
          
          <Button
            title="Schedule Appointment"
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
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
  },
  section: {
    marginBottom: Spacing.lg,
  },
  label: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.medium,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  clientScroll: {
    marginHorizontal: -Spacing.xs,
  },
  clientChip: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 20,
    marginHorizontal: Spacing.xs,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  clientChipActive: {
    backgroundColor: Colors.accent,
    borderColor: Colors.accent,
  },
  clientChipText: {
    fontSize: Typography.bodySmall,
    color: Colors.text,
    fontWeight: Typography.medium,
  },
  clientChipTextActive: {
    color: Colors.textInverse,
  },
  timeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -Spacing.xs,
  },
  timeSlot: {
    width: '22%',
    marginHorizontal: '1.5%',
    marginBottom: Spacing.sm,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  timeSlotActive: {
    backgroundColor: Colors.accent,
    borderColor: Colors.accent,
  },
  timeText: {
    fontSize: Typography.bodySmall,
    color: Colors.text,
    fontWeight: Typography.medium,
  },
  timeTextActive: {
    color: Colors.textInverse,
  },
  durationButtons: {
    flexDirection: 'row',
    marginHorizontal: -Spacing.xs,
  },
  durationButton: {
    flex: 1,
    marginHorizontal: Spacing.xs,
    paddingVertical: Spacing.md,
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  durationButtonActive: {
    backgroundColor: Colors.accent,
    borderColor: Colors.accent,
  },
  durationText: {
    fontSize: Typography.body,
    color: Colors.text,
    fontWeight: Typography.medium,
  },
  durationTextActive: {
    color: Colors.textInverse,
  },
  error: {
    fontSize: Typography.caption,
    color: Colors.error,
    marginTop: Spacing.xs,
  },
  saveButton: {
    marginTop: Spacing.md,
  },
});